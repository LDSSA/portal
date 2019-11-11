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
        executor.submit(run_simulator)

        # Start producer
        executor.submit(run_producer, submissions)

        while True:
            # Consume queue
            id_, url, data = submissions.get(block=True)
            executor.submit(consume, id_, url, data)


def run_simulator():
    while True:
        close_old_connections()

        with transaction.atomic():
            simulators = models.Simulator.objects.select_for_update().all()
            for simulator in simulators:
                simulator.reset()
                simulator.start()
                simulator.stop()

        time.sleep(settings.SIMULATOR_INTERVAL)


def run_producer(submissions):
    # Prevent thundering herd
    time.sleep(2 * random.random())
    qsize = 0

    while True:
        close_old_connections()

        # Retrieve a block of due datapoints
        with transaction.atomic():
            # Lock due datapoints
            # prevent multiple producers from repeating datapoints
            now = datetime.now(timezone.utc)
            qs = (models.DueDatapoint.objects
                  .select_for_update()
                  .filter(simulator__status='started')
                  .filter(state='due')
                  .filter(due__gte=now)
                  .select_related('student',
                                  'datapoint',
                                  'simulation'))[:settings.BLOCK_SIZE]

            items = []
            for obs in qs:
                url = obs.simulator.endpoint.format(
                    obs.student.app_name)

                items.append([obs.id, url, obs.datapoint.data])
                obs.status = 'queued'
                obs.save()

        # Queue due datapoints outside lock
        for item in items:
            submissions.put(item)

        # TODO
        old_qsize = qsize
        qsize = submissions.qsize()
        if old_qsize > 0 and qsize > old_qsize:
            logger.critical("Queue size increased this iteration")

        time.sleep(settings.PRODUCER_INTERVAL)


def consume(id_, url, data):
    close_old_connections()

    with transaction.atomic():
        due_datapoint = (models.Datapoint.objects
                         .select_for_update().get(id=id_))

        try:
            response = requests.post(url, json=data, timeout=settings.TIMEOUT)
        except requests.exceptions.RequestException as exc:
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
            due_datapoint.state = 'fail'
            due_datapoint.request_exception = exc.__class__.__name
            due_datapoint.request_traceback = traceback.format_tb(
                exc.__traceback__)
            due_datapoint.response_status = response.status_code
            due_datapoint.response_elapsed = response.elapsed.total_seconds()
            due_datapoint.response_content = response.text
            due_datapoint.save()
            return

        try:
            response.json()
            content = response.text

        except json.JSONDecodeError as exc:
            due_datapoint.state = 'fail'
            due_datapoint.request_exception = exc.__class__.__name
            due_datapoint.request_traceback = traceback.format_tb(
                exc.__traceback__)
            due_datapoint.response_status = response.status_code
            due_datapoint.response_elapsed = response.elapsed.total_seconds()
            due_datapoint.response_content = response.text
            due_datapoint.save()
            return

        else:
            due_datapoint.state = 'success'
            due_datapoint.response_content = content
            due_datapoint.response_status = response.status_code
            due_datapoint.response_elapsed = response.elapsed.total_seconds()
            due_datapoint.save()
