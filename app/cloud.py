import random
import string
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor

import requests
from config import settings
from libcloud.compute.base import Node
from libcloud.compute.base import NodeDriver
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from logger import logger
from models import VmTemplate
from models import WorkflowJobWebHook
from tenacity import retry
from tenacity import stop_after_delay
from tenacity import wait_fixed
from tenacity import wait_random


API_URL = "https://{ghe_host}/api/v3/repos/{owner}/{repo}/actions/runners/registration-token"


def get_registration_token(webhook: WorkflowJobWebHook) -> str:
    url = API_URL.format(
        ghe_host=settings.ghe_host,
        owner=webhook.repository.owner.login,
        repo=webhook.repository.name,
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.personal_access_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.post(url, headers=headers)
    data = resp.json()
    token = data["token"]
    logger.info(f"Got registration token for {webhook.repository.html_url}.")
    return token


class ConcurrencyException(Exception):
    def __init__(self, msg: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class Cloud:
    vm_templates: dict[str, VmTemplate]
    driver: NodeDriver

    def __init__(self) -> None:
        self.name = settings.env_for_dynaconf
        self.service_account = settings.driver_params.user_id
        self.instances: dict[str, Node] = {}

    def init(self) -> None:
        self.driver = self.driver or self._get_driver()
        self.vm_templates = self.vm_templates or self._get_vm_templates()

    def cleanup(self) -> None:
        logger.info(f"Shutting down running VMs: {len(self.instances)}.")
        with ThreadPoolExecutor() as executor:
            futures = {}
            for instance in self.instances.values():
                futures[executor.submit(instance.destroy)] = instance.name
            for future in as_completed(futures):
                name = futures[future]
                logger.info(f"Instance {name} has been destroyed.")

    def _get_driver(self) -> NodeDriver:
        driver_params = settings.driver_params
        Driver = get_driver(getattr(Provider, self.name.upper()))
        driver = Driver(**driver_params)
        logger.info(f"{self.name.upper()} driver has been initialized.")
        return driver

    def get_vm_template(self, webhook: WorkflowJobWebHook) -> VmTemplate | None:
        job_labels = set(webhook.workflow_job.labels)
        for _, template in self.vm_templates.items():
            if job_labels.issubset(set(template.labels)):
                return template
        logger.info(f"No runner with labels {webhook.workflow_job.labels}.")
        return None

    def _get_vm_templates(self) -> dict[str, VmTemplate]:
        vm_templates = {}
        with ThreadPoolExecutor() as executor:
            futures = {}
            for os, template in settings.vm_templates.items():
                futures[executor.submit(self.driver.ex_get_image, template.image)] = (os, template)
            for future in as_completed(futures):
                os, template = futures[future]
                image = future.result()
                logger.info(f"Found image {image.name}.")
                vm_templates[os] = VmTemplate(
                    image=image, size=template.size, labels=template.labels
                )
        return vm_templates

    @retry(stop=stop_after_delay(45 * 60), wait=wait_fixed(30) + wait_random(0, 5))
    def provision_vm(self, webhook: WorkflowJobWebHook, vm_template: VmTemplate) -> None:
        token = get_registration_token(webhook)
        random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        try:
            instance = self.driver.create_node(
                f"runner-{webhook.run_id}-{random_str}",
                size=vm_template.size,
                image=vm_template.image,
                ex_metadata={
                    "repo_url": webhook.repository.html_url,
                    "token": token,
                    "labels": ",".join(vm_template.labels),
                },
                ex_service_accounts=[{"email": self.service_account, "scopes": ["compute"]}],
            )
        except Exception as e:
            logger.error(f"Unable to provision an instance: {str(e)}. Retrying.")
            raise
        logger.info(f"Instance {instance.name} has been created.")
        self.instances[instance.name] = instance

    def destroy_vm(self, webhook: WorkflowJobWebHook) -> None:
        instance = self.instances[webhook.runner_name]
        if instance.destroy():
            del self.instances[webhook.runner_name]
            logger.info(f"Instance {webhook.runner_name} has been destroyed.")


cloud = Cloud()
