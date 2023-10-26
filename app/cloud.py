import random
import string

import requests
from config import settings
from libcloud.compute.base import Node
from libcloud.compute.base import NodeDriver
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from logger import logger
from models import WorkflowJobWebHook


API_URL = "https://{ghe_host}/api/v3/repos/{owner}/{repo}/actions/runners/registration-token"


class Cloud:
    def __init__(self) -> None:
        self.name = settings.cloud
        self.service_account = settings[self.name].driver_params.user_id
        self.driver: NodeDriver
        self.images: dict[str, dict[str, str]]
        self.instances: dict[str, Node] = {}

    def init(self):
        if not self.driver:
            self.driver = self._get_driver()
        if not self.images:
            self.images = self._get_images()

    def cleanup(self):
        logger.info(f"Shutting down running VMs: {len(self.instances)}.")
        for instance in self.instances.values():
            instance.destroy()
            logger.info(f"Instance {instance.name} has been destroyed.")

    def _get_driver(self) -> NodeDriver:
        driver_params = settings[self.name].driver_params
        Driver = get_driver(getattr(Provider, settings.cloud.upper()))
        driver = Driver(**driver_params)
        logger.info(f"{self.name.upper()} driver has been initialized.")
        return driver

    def _get_images(self) -> dict[str, dict[str, str]]:
        images = {}
        for os, template in settings[self.name].vm_templates.items():
            image = self.driver.ex_get_image(template.image)
            logger.info(f"Found image {image.name}")
            images[os] = {"image": image, "size": template.size}
        return images


cloud = Cloud()


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


def provision_vm(webhook: WorkflowJobWebHook, os: str) -> None:
    token = get_registration_token(webhook)
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    instance = cloud.driver.create_node(
        f"runner-{os}-{random_str}",
        size=cloud.images[os]["size"],
        image=cloud.images[os]["image"],
        ex_metadata={"repo_url": webhook.repository.html_url, "token": token},
        ex_service_accounts=[{"email": cloud.service_account, "scopes": ["compute"]}],
    )
    logger.info(f"{webhook.job_id}: Instance {instance.name} has been created.")
    cloud.instances[instance.name] = instance


def destroy_vm(webhook: WorkflowJobWebHook) -> None:
    instance = cloud.instances[webhook.runner_name]
    if instance.destroy():
        del cloud.instances[webhook.runner_name]
        logger.info(f"{webhook.job_id}: Instance {webhook.runner_name} has been destroyed.")
