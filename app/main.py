#!/usr/bin/env python3

from fastapi import FastAPI
from models import Action, WorkflowJobWebHook
from clouds import provision_vm
from clouds import destroy_vm
from config import settings

import requests
import uvicorn


app = FastAPI()

API_URL = "https://{ghe_host}/api/v3/repos/{owner}/{repo}/actions/runners/registration-token"


def get_registration_token(webhook: WorkflowJobWebHook) -> str:
    url = API_URL.format(
        ghe_host=settings.ghe_host,
        owner=webhook.repository.owner.login,
        repo=webhook.repository.name
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.personal_access_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    resp = requests.post(url, headers=headers)
    data = resp.json()
    return data["token"]


@app.post("/actions")
def actions(webhook: WorkflowJobWebHook):
    if webhook.action == Action.queued:
        token = get_registration_token(webhook)
        provision_vm(webhook.repository.html_url, token)
    if webhook.action == Action.completed:
        destroy_vm(webhook.workflow_job.runner_name)


def start():
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="error")


if __name__ == "__main__":
    start()
