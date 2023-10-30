import threading

from cloud import cloud
from models import VmTemplate
from models import WorkflowJobWebHook


events = {}


def queue(webhook: WorkflowJobWebHook, vm_template: VmTemplate) -> None:
    event = events[webhook.job_url] = threading.Event()
    cloud.provision_vm(webhook, vm_template)
    event.wait()


def complete(webhook: WorkflowJobWebHook) -> None:
    cloud.destroy_vm(webhook)
    event = events[webhook.job_url]
    event.set()
