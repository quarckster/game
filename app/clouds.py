import random
import string
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from config import settings

instances = {}

Driver = get_driver(getattr(Provider, settings.cloud.name.upper()))
driver = Driver(**settings.cloud.driver_params)
vm_size = driver.ex_get_size(settings.cloud.vm_size)


def provision_vm(repo_url: str, token: str, labels: list[str]) -> None:
    random_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    image = driver.ex_get_image(labels[0])
    instance = driver.create_node(
        f"{image.name}-{random_str}",
        vm_size,
        image,
        ex_metadata={"repo_url": repo_url, "token": token},
        ex_service_accounts=[{
            "email": settings.cloud.driver_params.user_id,
            "scopes": ["compute"]
        }]
    )
    print(f"instance {instance.name} has been created")
    instances[instance.name] = instance


def destroy_vm(name: str) -> None:
    print(f"destroying instance {name}")
    instance = instances[name]
    instance.destroy()
