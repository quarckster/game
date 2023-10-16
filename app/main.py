#!/usr/bin/env python3
import requests
import uvicorn
from cloud import destroy_vm
from cloud import provision_vm
from config import settings
from fastapi import FastAPI
from models import Action
from models import WorkflowJobWebHook


app = FastAPI()

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
    return data["token"]


@app.post("/actions")
def actions(webhook: WorkflowJobWebHook):
    if webhook.action == Action.queued:
        token = get_registration_token(webhook)
        provision_vm(webhook.repository.html_url, token, webhook.workflow_job.labels)
    if webhook.action == Action.completed and webhook.workflow_job.runner_name:
        destroy_vm(webhook.workflow_job.runner_name)


def start():
    print("Waiting for workflow_job webhooks")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="error")


if __name__ == "__main__":
    start()
