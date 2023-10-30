import threading

from cloud import cloud
from models import VmTemplate
from models import WorkflowJobWebHook


events = {}


def queue(webhook: WorkflowJobWebHook, vm_template: VmTemplate) -> None:
    runner_name = cloud.provision_vm(webhook, vm_template)
    event = events[runner_name] = threading.Event()
    event.wait()
    del events[runner_name]


def complete(webhook: WorkflowJobWebHook) -> None:
    cloud.destroy_vm(webhook)
    event = events[webhook.runner_name]
    event.set()
