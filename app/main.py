#!/usr/bin/env python3
from contextlib import asynccontextmanager

import uvicorn
from cloud import cloud
from cloud import destroy_vm
from cloud import provision_vm
from config import settings
from fastapi import BackgroundTasks
from fastapi import FastAPI
from logger import logger
from models import Action
from models import WorkflowJobWebHook


@asynccontextmanager
async def lifespan(app: FastAPI):
    cloud.init()
    yield


app = FastAPI(lifespan=lifespan)


def get_image_os(webhook: WorkflowJobWebHook) -> str | None:
    job_labels = set(webhook.workflow_job.labels)
    for os, predefined_labels in settings.labels.items():
        if job_labels.issubset(set(predefined_labels)):
            return os
    logger.info(f"No runner with labels {webhook.workflow_job.labels}")
    return None


@app.post("/actions")
async def actions(webhook: WorkflowJobWebHook, background_tasks: BackgroundTasks):
    if webhook.action == Action.queued and (image_os := get_image_os(webhook)):
        logger.info(f"{webhook.workflow_job.id}: Job queued")
        background_tasks.add_task(provision_vm, webhook, image_os)
    if webhook.action == Action.completed and webhook.workflow_job.runner_name:
        logger.info(f"{webhook.workflow_job.id}: Job completed")
        background_tasks.add_task(destroy_vm, webhook)


def start():
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    start()
