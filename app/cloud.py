import random
import string

from config import settings
from libcloud.compute.base import Node
from libcloud.compute.providers import get_driver
from libcloud.compute.types import Provider
from logger import logger


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


def provision_vm(repo_url: str, token: str, os: str) -> None:
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    instance = cloud.driver.create_node(
        f"runner-{os}-{random_str}",
        cloud.images[os]["image"],
        cloud.images[os]["size"],
        ex_metadata={"repo_url": repo_url, "token": token},
        ex_service_accounts=[
            {"email": settings.cloud.driver_params.user_id, "scopes": ["compute"]}
        ],
    )
    logger.info(f"Instance {instance.name} has been created")
    instances[instance.name] = instance


def destroy_vm(name: str) -> None:
    instance = instances[name]
    instance.destroy()
    logger.info(f"Instance {name} has been destroyed")
