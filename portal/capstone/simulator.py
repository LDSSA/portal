import json
import logging
import queue
import random
import time
import traceback
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from datetime import datetime, timezone

import requests
from django.db import transaction, close_old_connections
from django.conf import settings

from portal.capstone import models


logger = logging.getLogger(__name__)


def run():
    # Queue
    submissions = queue.Queue()

    # Start consumer pool
    with PoolExecutor(max_workers=10) as executor:
        # Start simulator
        logger.info("Starting simulator..")
        executor.submit(run_simulator)

        # Start producer
        logger.info("Starting producer...")
        executor.submit(run_producer, submissions)

        logger.info("Starting consumer...")
        while True:
            # Consume queue
            id_ = submissions.get(block=True)
            executor.submit(consume, id_)


def run_simulator():
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


def run_producer(submissions):
    # Prevent thundering herd
    time.sleep(2 * random.random())

    while True:
        logger.debug("Producer cycle...")
        close_old_connections()

        try:
            # Retrieve a block of due datapoints
            with transaction.atomic():
                # Lock due datapoints
                # prevent multiple producers from repeating datapoints
                now = datetime.now(timezone.utc)
                qs = (models.DueDatapoint.objects
                      .select_for_update()
                      .filter(simulator__status='started')
                      .filter(state='due')
                      .filter(due__lte=now))[:settings.BLOCK_SIZE]

                items = []
                for due_datapoint in qs:
                    items.append(due_datapoint.id)
                    due_datapoint.status = 'queued'
                    due_datapoint.save()

            # Queue due datapoints outside lock
            if items:
                logger.info('Queuing due datapoints')
            for item in items:
                logger.info("Producing %s", item)
                submissions.put(item)

            logger.debug("Queue size: %s", submissions.qsize())

        except Exception:
            logger.exception("Exception in producer")

        time.sleep(settings.PRODUCER_INTERVAL)


# TODO mark as due any unconsumed due datapoints
def consume(id_):
    close_old_connections()
    logger.info("Consuming %s", id_)

    try:
        with transaction.atomic():
            due_datapoint = (models.DueDatapoint.objects
                             .select_related('datapoint')
                             .select_for_update().get(id=id_))

            try:
                logger.info("Posting %s", id_)
                data = json.loads(due_datapoint.datapoint.data)
                response = requests.post(due_datapoint.url,
                                         json=data,
                                         timeout=settings.TIMEOUT)

            except requests.exceptions.RequestException as exc:
                logger.info("Request Exception %s", id_, exc_info=True)
                due_datapoint.state = 'fail'
                due_datapoint.request_exception = exc.__class__.__name__
                due_datapoint.request_traceback = traceback.format_tb(
                    exc.__traceback__)
                if isinstance(exc, requests.exceptions.Timeout):
                    due_datapoint.response_timeout = True
                due_datapoint.save()
                return

            try:
                response.raise_for_status()

            except requests.exceptions.HTTPError as exc:
                logger.info("HTTP Exception %s", id_, exc_info=True)
                due_datapoint.state = 'fail'
                due_datapoint.request_exception = exc.__class__.__name__
                due_datapoint.request_traceback = traceback.format_tb(
                    exc.__traceback__)
                due_datapoint.response_status = response.status_code
                due_datapoint.response_elapsed = (response.elapsed
                                                  .total_seconds())
                due_datapoint.response_content = response.text
                due_datapoint.save()
                return

            try:
                response.json()
                content = response.text

            except json.JSONDecodeError as exc:
                logger.info("Response Exception %s", id_, exc_info=True)

                due_datapoint.state = 'fail'
                due_datapoint.request_exception = exc.__class__.__name__
                due_datapoint.request_traceback = traceback.format_tb(
                    exc.__traceback__)
                due_datapoint.response_status = response.status_code
                due_datapoint.response_elapsed = (response.elapsed
                                                  .total_seconds())
                due_datapoint.response_content = response.text
                due_datapoint.save()
                return

            else:
                logger.info("Success %s", id_)
                due_datapoint.state = 'success'
                due_datapoint.response_content = content
                due_datapoint.response_status = response.status_code
                due_datapoint.response_elapsed = (response.elapsed
                                                  .total_seconds())
                due_datapoint.save()

    except Exception:
        logger.exception("Exception consuming %s", id_)
