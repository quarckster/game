#!/usr/bin/env python3
from contextlib import asynccontextmanager

import requests
import uvicorn
from cloud import cloud
from cloud import destroy_vm
from cloud import provision_vm
from config import settings
from fastapi import FastAPI
from logger import logger
from models import Action
from models import WorkflowJobWebHook


API_URL = "https://{ghe_host}/api/v3/repos/{owner}/{repo}/actions/runners/registration-token"


@asynccontextmanager
async def lifespan(app: FastAPI):
    cloud.init()
    yield


app = FastAPI(lifespan=lifespan)


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
    logger.info("Got registration token")
    return token


def get_image_os(webhook: WorkflowJobWebHook) -> str | None:
    job_labels = set(webhook.workflow_job.labels)
    for os, predefined_labels in settings.labels.items():
        if job_labels.issubset(set(predefined_labels)):
            return os
    logger.info(f"No runner with labels {webhook.workflow_job.labels}")
    return None


@app.post("/actions")
def actions(webhook: WorkflowJobWebHook):
    if webhook.action == Action.queued and (image_os := get_image_os(webhook)):
        logger.info("Queued")
        token = get_registration_token(webhook)
        provision_vm(webhook.repository.html_url, token, image_os)
    if webhook.action == Action.completed and webhook.workflow_job.runner_name:
        logger.info("Completed")
        destroy_vm(webhook.workflow_job.runner_name)


def start():
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")


if __name__ == "__main__":
    start()
