import asyncio
from datetime import datetime
import logging
import sys

from automation_server_client import AutomationServer, Workqueue, WorkItemError, Credential, WorkItemStatus
from odk_tools.tracking import Tracker
from xflow_client import XFlowClient, ProcessClient
from kmd_nexus_client.tree_helpers import (
    filter_by_predicate,
)

xflow_client: XFlowClient
xflow_process_client: ProcessClient


async def populate_queue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from populate workqueue!")

    xlow_søge_query = {
        "text": "",
        "processTemplateIds": ["753"], # skal have id fra benner
        "startIndex": 0,
        "createdDateFrom": "01-01-1980",
        "createdDateTo": datetime.today().strftime("%d-%m-%Y"),
    }

    igangværende_processer = xflow_process_client.search_processes_by_current_activity(
        query=xlow_søge_query,
        activity_name="RPAIntegration",
    )

    for proces in igangværende_processer:
        blanketter = proces["blanketter"]

        samlet_ansøgning = filter_by_predicate(
            roots=blanketter, predicate=lambda x: x["blanketnavn"] == "SBH - Samlet" # skal have navn fra benner
        )


async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from process workqueue!")

    for item in workqueue:
        with item:
            data = item.data  # Item data deserialized from json as dict
 
            try:
                # Process the item here
                pass
            except WorkItemError as e:
                # A WorkItemError represents a soft error that indicates the item should be passed to manual processing or a business logic fault
                logger.error(f"Error processing item: {data}. Error: {e}")
                item.fail(str(e))


if __name__ == "__main__":
    ats = AutomationServer.from_environment()
    workqueue = ats.workqueue()

    # Initialize external systems for automation here..
    xflow_credential = Credential.get_credential("Xflow - produktion")
    tracking_credential = Credential.get_credential("Odense SQL Server")

    xflow_client = XFlowClient(
        token=xflow_credential.password,
        instance=xflow_credential.data["instance"],
    )
    xflow_process_client = ProcessClient(xflow_client)

    tracker = Tracker(
        username=tracking_credential.username, password=tracking_credential.password
    )


    # Queue management
    if "--queue" in sys.argv:
        workqueue.clear_workqueue(WorkItemStatus.NEW)
        asyncio.run(populate_queue(workqueue))
        exit(0)

    # Process workqueue
    asyncio.run(process_workqueue(workqueue))
