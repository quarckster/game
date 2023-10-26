import random
import string

import requests
from config import settings
from libcloud.compute.base import Node
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from logger import logger
from models import WorkflowJobWebHook


API_URL = "https://{ghe_host}/api/v3/repos/{owner}/{repo}/actions/runners/registration-token"

instances: dict[str, Node] = {}

cloud_name = settings.cloud


class Cloud:
    def __init__(self):
        self.driver = None
        self.images = None

    def init(self):
        if not self.driver:
            self.driver = self._get_driver()
        if not self.images:
            self.images = self._get_images()

    def _get_driver(self):
        driver_params = settings[cloud_name].driver_params
        Driver = get_driver(getattr(Provider, settings.cloud.upper()))
        driver = Driver(**driver_params)
        logger.info(f"{cloud_name.upper()} driver has been initialized")
        return driver

    def _get_images(self) -> dict[str, dict[str, str]]:
        images = {}
        for os, template in settings[cloud_name].vm_templates.items():
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
    logger.info(f"{webhook.workflow_job.id}: Got registration token")
    return token


def provision_vm(webhook: WorkflowJobWebHook, os: str) -> None:
    token = get_registration_token(webhook)
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    instance = cloud.driver.create_node(
        f"runner-{os}-{random_str}",
        size=cloud.images[os]["size"],
        image=cloud.images[os]["image"],
        ex_metadata={"repo_url": webhook.repository.html_url, "token": token},
        ex_service_accounts=[
            {"email": settings[cloud_name].driver_params.user_id, "scopes": ["compute"]}
        ],
    )
    logger.info(f"{webhook.workflow_job.id}: Instance {instance.name} has been created")
    instances[instance.name] = instance


def destroy_vm(webhook: WorkflowJobWebHook) -> None:
    runner_name = webhook.workflow_job.runner_name
    instance = instances[runner_name]
    instance.destroy()
    logger.info(f"{webhook.workflow_job.id}: Instance {runner_name} has been destroyed")
