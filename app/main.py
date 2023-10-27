#!/usr/bin/env python3
from contextlib import asynccontextmanager

import uvicorn
from cloud import cloud
from config import settings
from fastapi import BackgroundTasks
from fastapi import FastAPI
from logger import log_config
from logger import logger
from models import Action
from models import WorkflowJobWebHook


@asynccontextmanager
async def lifespan(app: FastAPI):
    cloud.init()
    yield
    cloud.cleanup()


app = FastAPI(lifespan=lifespan)


@app.post("/actions")
async def actions(webhook: WorkflowJobWebHook, background_tasks: BackgroundTasks):
    if webhook.action == Action.queued and (vm_template := cloud.get_vm_template(webhook)):
        logger.info(f'{webhook.job_id}: Job "{webhook.job_name}" queued.')
        background_tasks.add_task(cloud.provision_vm, webhook, vm_template)
    if webhook.action == Action.completed and webhook.workflow_job.runner_name:
        logger.info(f'{webhook.job_id}: Job "{webhook.job_name}" completed.')
        background_tasks.add_task(cloud.destroy_vm, webhook)


def start():
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=log_config)


if __name__ == "__main__":
    start()
