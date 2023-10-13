import random
import string
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from config import settings

instances = {}

Driver = get_driver(getattr(Provider, settings.cloud.name.upper()))
driver = Driver(
    settings.cloud.service_account,
    settings.cloud.private_key,
    project=settings.cloud.project,
    datacenter=settings.cloud.zone
)

image = driver.ex_get_image("linux-runner")
size = driver.ex_get_size("e2-standard-2")

def provision_vm(repo_url: str, token: str) -> None:
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    instance = driver.create_node(
        f"linux-runner-{random_str}",
        size,
        image,
        ex_metadata={"repo_url": repo_url, "token": token},
        ex_service_accounts=[{
            "email": settings.cloud.service_account,
            "scopes": ["compute"]
        }]
    )
    print(f"instance {instance.name} has been created")
    instances[instance.name] = instance


def destroy_vm(name: str) -> None:
    print(f"destroying instance {name}")
    instance = instances[name]
    instance.destroy()
