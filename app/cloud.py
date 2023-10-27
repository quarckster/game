import random
import string

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
    logger.info(f"{webhook.job_id}: Got registration token for {webhook.repository.html_url}.")
    return token


class Cloud:
    def __init__(self) -> None:
        self.name = settings.env_for_dynaconf
        self.service_account = settings.driver_params.user_id
        self.driver: NodeDriver = None
        self.vm_templates: dict[str, VmTemplate] = None
        self.instances: dict[str, Node] = {}

    def init(self):
        self.driver = self.driver or self._get_driver()
        self.vm_templates = self.vm_templates or self._get_vm_templates()

    def cleanup(self):
        logger.info(f"Shutting down running VMs: {len(self.instances)}.")
        for instance in self.instances.values():
            instance.destroy()
            logger.info(f"Instance {instance.name} has been destroyed.")

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
        logger.info(f"{webhook.job_id}: No runner with labels {webhook.workflow_job.labels}.")
        return None

    def _get_vm_templates(self) -> dict[str, VmTemplate]:
        vm_templates = {}
        for os, template in settings.vm_templates.items():
            image = self.driver.ex_get_image(template.image)
            logger.info(f"Found image {image.name}.")
            vm_templates[os] = VmTemplate(image=image, size=template.size, labels=template.labels)
        return vm_templates

    def provision_vm(self, webhook: WorkflowJobWebHook, vm_template: VmTemplate) -> None:
        token = get_registration_token(webhook)
        random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        instance = self.driver.create_node(
            f"runner-{webhook.run_id}-{webhook.job_id}-{random_str}",
            size=vm_template.size,
            image=vm_template.image,
            ex_metadata={
                "repo_url": webhook.repository.html_url,
                "token": token,
                "labels": ",".join(vm_template.labels),
            },
            ex_service_accounts=[{"email": self.service_account, "scopes": ["compute"]}],
        )
        logger.info(f"{webhook.job_id}: Instance {instance.name} has been created.")
        self.instances[instance.name] = instance

    def destroy_vm(self, webhook: WorkflowJobWebHook) -> None:
        instance = self.instances[webhook.runner_name]
        if instance.destroy():
            del self.instances[webhook.runner_name]
            logger.info(f"{webhook.job_id}: Instance {webhook.runner_name} has been destroyed.")


cloud = Cloud()
