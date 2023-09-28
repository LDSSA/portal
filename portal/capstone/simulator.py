import json  # noqa: D100
import logging
import random
import time
import traceback
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from datetime import datetime, timezone

import requests
from django.conf import settings
from django.db import DatabaseError, close_old_connections, transaction

from portal.capstone import models

logger = logging.getLogger(__name__)
WORKERS = 50


def run():  # noqa: D103
    # Queue

    # Start consumer pool
    with PoolExecutor(max_workers=WORKERS) as executor:
        # Start simulator
        logger.info("Starting simulator..")
        executor.submit(run_simulator)

        # Start producer
        for idx in range(WORKERS - 1):
            logger.info("Starting producer %s...", idx)
            executor.submit(run_producer)


def run_simulator():  # noqa: D103
    while True:
        logger.debug("Simulator cycle...")
        close_old_connections()

        try:
            with transaction.atomic():
                simulators = models.Simulator.objects.select_for_update().all()
                for simulator in simulators:
                    simulator.reset()
                    simulator.start()

        except Exception:
            logger.exception("Exception in simulator")

        time.sleep(settings.SIMULATOR_INTERVAL)


def run_producer():  # noqa: D103
    # Prevent thundering herd
    time.sleep(2 * random.random())

    while True:
        time.sleep(settings.PRODUCER_INTERVAL)
        logger.debug("Producer cycle...")
        close_old_connections()

        # If no simulator is running wait for longer
        if not models.Simulator.objects.filter(status="started").exists():
            time.sleep(settings.SIMULATOR_INTERVAL)
            continue

        try:
            # Retrieve a due datapoints
            with transaction.atomic():
                # Lock due datapoints
                # prevent multiple producers from repeating datapoints
                now = datetime.now(timezone.utc)
                try:
                    due_datapoint = (
                        models.DueDatapoint.objects.select_for_update(nowait=True)
                        .order_by("due")
                        .filter(state="queued")
                        .filter(simulator__status="started")
                        .filter(due__lte=now)
                        .first()
                    )
                except DatabaseError:
                    logger.debug("Unable to aquire lock")
                    continue
                if due_datapoint is None:
                    continue
                logger.debug("Locked %s", due_datapoint.id)
                due_datapoint.state = "due"
                due_datapoint.save()

            send_datapoint(due_datapoint)
        except Exception:
            logger.exception("Exception in producer")


def send_datapoint(due_datapoint):  # noqa: D103
    try:
        try:
            logger.info(
                "Posting %s %s %s", due_datapoint.id, due_datapoint.user.username, due_datapoint.due
            )
            data = json.loads(due_datapoint.datapoint.data)
            response = requests.post(due_datapoint.url, json=data, timeout=settings.TIMEOUT)

        except requests.exceptions.RequestException as exc:
            logger.info("Student API Request Exception %s", due_datapoint.id, exc_info=True)

            due_datapoint.state = "fail"
            due_datapoint.response_exception = exc.__class__.__name__
            due_datapoint.response_traceback = traceback.format_tb(exc.__traceback__)
            if isinstance(exc, requests.exceptions.Timeout):
                due_datapoint.response_timeout = True
            due_datapoint.save()
            return

        try:
            response.raise_for_status()

        except requests.exceptions.HTTPError as exc:
            logger.info("HTTP Exception %s", due_datapoint.id, exc_info=True)
            due_datapoint.state = "fail"
            due_datapoint.response_exception = exc.__class__.__name__
            due_datapoint.response_traceback = traceback.format_tb(exc.__traceback__)
            due_datapoint.response_status = response.status_code
            due_datapoint.response_elapsed = response.elapsed.total_seconds()
            due_datapoint.response_content = response.text
            due_datapoint.save()
            return

        try:
            response.json()
            content = response.text

        except json.JSONDecodeError as exc:
            logger.info("Response Exception %s", due_datapoint.id, exc_info=True)

            due_datapoint.state = "fail"
            due_datapoint.response_exception = exc.__class__.__name__
            due_datapoint.response_traceback = traceback.format_tb(exc.__traceback__)
            due_datapoint.response_status = response.status_code
            due_datapoint.response_elapsed = response.elapsed.total_seconds()
            due_datapoint.response_content = response.text
            due_datapoint.save()
            return

        else:
            logger.info("Success %s", due_datapoint.id)
            due_datapoint.state = "success"
            due_datapoint.response_content = content
            due_datapoint.response_status = response.status_code
            due_datapoint.response_elapsed = response.elapsed.total_seconds()
            due_datapoint.save()

    except Exception:
        logger.exception("Exception consuming %s", due_datapoint.id)
