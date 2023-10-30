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


class Cloud:
    def __init__(self) -> None:
        self.name = settings.env_for_dynaconf
        self.service_account = settings.driver_params.user_id
        self.instances: dict[str, Node] = {}
        self.vm_templates: list[VmTemplate] = []
        for _, template in settings.vm_templates.items():
            self.vm_templates.append(
                VmTemplate(image=template.image, size=template.size, labels=template.labels)
            )

    def cleanup(self) -> None:
        logger.info(f"Shutting down running VMs: {len(self.instances)}.")
        with ThreadPoolExecutor() as executor:
            futures = {}
            for instance in self.instances.values():
                futures[executor.submit(instance.destroy)] = instance.name
            for future in as_completed(futures):
                name = futures[future]
                logger.info(f"Instance {name} has been destroyed.")

    def get_driver(self) -> NodeDriver:
        """
        Libcloud driver instance is not thread safe. The documentation recommends to create a new
        driver instance inside each thread.
        https://libcloud.readthedocs.io/en/stable/other/using-libcloud-in-multithreaded-and-async-environments.html
        """
        driver_params = settings.driver_params
        Driver = get_driver(getattr(Provider, self.name.upper()))
        return Driver(**driver_params)

    def get_vm_template(self, webhook: WorkflowJobWebHook) -> VmTemplate | None:
        job_labels = set(webhook.workflow_job.labels)
        for template in self.vm_templates:
            if job_labels.issubset(set(template.labels)):
                return template
        logger.info(f"No runner with labels {webhook.workflow_job.labels}.")
        return None

    def provision_vm(self, webhook: WorkflowJobWebHook, vm_template: VmTemplate) -> None:
        token = get_registration_token(webhook)
        random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        driver = self.get_driver()
        image = driver.ex_get_image(vm_template.image)
        instance = driver.create_node(
            f"runner-{webhook.run_id}-{random_str}",
            size=vm_template.size,
            image=image,
            ex_metadata={
                "repo_url": webhook.repository.html_url,
                "token": token,
                "labels": ",".join(vm_template.labels),
            },
            ex_service_accounts=[{"email": self.service_account, "scopes": ["compute"]}],
        )
        logger.info(f"Instance {instance.name} has been created.")
        self.instances[instance.name] = instance

    def destroy_vm(self, webhook: WorkflowJobWebHook) -> None:
        instance = self.instances[webhook.runner_name]
        if instance.destroy():
            del self.instances[webhook.runner_name]
            logger.info(f"Instance {webhook.runner_name} has been destroyed.")


cloud = Cloud()
