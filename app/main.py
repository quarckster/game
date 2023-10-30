#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import job
import uvicorn
from cloud import cloud
from config import settings
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
    queue_executor.shutdown(cancel_futures=True)
    complete_executor.shutdown(cancel_futures=True)


app = FastAPI(lifespan=lifespan)
queue_executor = ThreadPoolExecutor(max_workers=settings.concurrency)
complete_executor = ThreadPoolExecutor()


@app.post("/actions")
async def actions(webhook: WorkflowJobWebHook):
    if webhook.action == Action.queued and (vm_template := cloud.get_vm_template(webhook)):
        queue_executor.submit(job.queue, webhook, vm_template)
        logger.info(f'Workflow "{webhook.workflow_name}" job "{webhook.job_name}" queued.')
    if webhook.action == Action.completed and webhook.workflow_job.runner_name:
        complete_executor.submit(job.complete, webhook)
        logger.info(f'Workflow "{webhook.workflow_name}" job "{webhook.job_name}" completed.')
    if webhook.action == Action.in_progress:
        logger.info(f'Workflow "{webhook.workflow_name}" job "{webhook.job_name}" in progress.')


def start():
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=log_config)


if __name__ == "__main__":
    start()
