import asyncio
from datetime import datetime
from rapidfuzz.distance import Levenshtein
import logging
import sys

from automation_server_client import (
    AutomationServer,
    Workqueue,
    WorkItemError,
    Credential,
    WorkItemStatus,
)
from odk_tools.tracking import Tracker
from sbsys.manager import SbsysClientManager

# from sbsys.models import Skabelon, Sag
from xflow_client import XFlowClient, ProcessClient
from process.xflow import afsend_til_xflow
from kmd_nexus_client.tree_helpers import (
    filter_by_predicate,
)

xflow_client: XFlowClient
xflow_process_client: ProcessClient
sbsys: SbsysClientManager
procesnavn = "Farlig skolevej"


def hent_værdi(elementer, identifier, key):
    match = filter_by_predicate(
        roots=elementer, predicate=lambda x: x["identifier"] == identifier
    )
    return match[0].get("values", {}).get(key) if match else None


async def populate_queue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from populate workqueue!")

    xlow_søge_query = {
        "text": "",
        "processTemplateIds": ["811"],  # skal have id fra benner
        "startIndex": 0,
        "createdDateFrom": "01-01-1980",
        "createdDateTo": datetime.today().strftime("%d-%m-%Y"),
    }

    igangværende_processer = xflow_process_client.search_processes_by_current_activity(
        query=xlow_søge_query,
        activity_name="RPAIntegration",
    )

    blanketnavne = [
        "Elevbefordring 0.-9. klasse - Vurdering (ny)",
        "Elevbefordring 0.-9. klasse - oplysninger om udfylder og barnet (ny)",
    ]

    for proces in igangværende_processer:
        blanketter = proces["blanketter"]

        samlet_ansøgning = filter_by_predicate(
            roots=blanketter, predicate=lambda x: x["blanketnavn"] == blanketnavne[0]
        ) + filter_by_predicate(
            roots=blanketter, predicate=lambda x: x["blanketnavn"] == blanketnavne[1]
        )

        barnets_adresse = hent_værdi(
            samlet_ansøgning[0]["elementer"], "ElementAdresse", "Adresse"
        )
        barnets_klasse = hent_værdi(
            samlet_ansøgning[0]["elementer"],
            "ElementVaerdilisteKlassetrin",
            "Valgtevaerdi",
        )
        barnets_cpr = hent_værdi(
            samlet_ansøgning[1]["elementer"], "BarnetsOplysninger", "CprNummer"
        )

        data = {
            "procesid": proces["publicId"],
            "barnets_cpr": barnets_cpr,
            "barnets_klasse": barnets_klasse,
            "barnets_adresse": barnets_adresse,
        }
        workqueue.add_item(data, barnets_cpr)


async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from process workqueue!")

    for item in workqueue:
        with item:
            data = item.data  # Item data deserialized from json as dict
            try:
                async with sbsys:
                    #   borger = await sbsys.borger.hent_borger(data["barnets_cpr"])
                    borgers_sager = await sbsys.sager.hent_sager_på_borger(
                        data["barnets_cpr"]
                    )

                borgers_sager = [
                    sag
                    for sag in borgers_sager
                    if "Indskrivning Klasse" in sag.get("SagsTitel", "")
                ]  # Behold kun indskrivningssager
                if not borgers_sager:
                    raise WorkItemError(
                        f"Borger med CPR {data['barnets_cpr']} har ingen indskrivningssager i sbsys."
                    )
                # adresse = borger["Adresse"]["Adresse1"] + ", " + borger["Adresse"]["Bynavn"] + ", " + str(borger["Adresse"]["PostNummer"]) + " " + borger["Adresse"]["PostDistrikt"]

                # Checker om adressen i xflow og sbsys er ens nok, hvis ikke sendes den til manuel behandling
                # distance = Levenshtein.distance(adresse.lower(), data["barnets_adresse"].lower())
                # til_manuel = distance / max(len(adresse), len(data["barnets_adresse"])) > 0.10

                afsend_til_xflow(
                    xflow_process_client,
                    data["procesid"],
                    borgers_sager[0]["SagsTitel"],
                )

                tracker.track_task(process_name=procesnavn)

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
    sbsys_credential = Credential.get_credential("SBSYS - produktion")

    xflow_client = XFlowClient(
        token=xflow_credential.password,
        instance=xflow_credential.data["instance"],
    )
    xflow_process_client = ProcessClient(xflow_client)

    tracker = Tracker(
        username=tracking_credential.username, password=tracking_credential.password
    )

    sbsys = SbsysClientManager(
        sbsys_credential.data["base_url"],
        sbsys_credential.data["token_url"],
        sbsys_credential.data["client_id"],
        sbsys_credential.data["client_secret"],
        sbsys_credential.username,
        sbsys_credential.password,
    )

    # Queue management
    if "--queue" in sys.argv:
        workqueue.clear_workqueue(WorkItemStatus.NEW)
        asyncio.run(populate_queue(workqueue))
        exit(0)

    # Process workqueue
    asyncio.run(process_workqueue(workqueue))
