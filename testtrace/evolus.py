"""Evolus Manufacturing Schedule & Work Order Integration for TestTrace Guard."""

import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Optional
import uuid

import httpx

from testtrace.schemas import EvolusTicket, PipelineRunResult

logger = logging.getLogger("testtrace.evolus")

DEFAULT_EVOLUS_DIR = Path("data/evolus")


def create_evolus_ticket(
    result: PipelineRunResult,
    priority_override: Optional[str] = None,
) -> EvolusTicket:
    """Map a PipelineRunResult into an actionable Evolus MES work order or FA quarantine ticket."""
    rep = result.report
    cat = rep.category
    case_id = result.case_id
    run_id = result.run_id
    sop = rep.primary_kb_doc
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    ticket_uid = f"EVO-{uuid.uuid4().hex[:8].upper()}"

    if result.analytics.affected_stations:
        target_station = result.analytics.affected_stations[0]
    else:
        target_station = "ST-A"

    if cat == "STATION_CONFIGURATION":
        ticket_type = "STATION_MAINTENANCE_HALT"
        target_entity = f"Station_{target_station}"
        priority = priority_override or "CRITICAL"
        title = f"HALT {target_entity}: Station Cable Loss Offset & Config Drift"
        desc = (
            f"Automated line halt triggered by TestTrace Guard for {target_entity}. "
            f"Systematic insertion loss delta detected. Execute {sop} corrective baseline restoration."
        )
    elif cat == "DUT_DEFECT":
        ticket_type = "DUT_FAILURE_ANALYSIS_QUARANTINE"
        target_entity = "DUT_017"
        priority = priority_override or "HIGH"
        title = f"QUARANTINE {target_entity}: Intrinsic RF Defect & LO Leakage"
        desc = (
            f"Target unit {target_entity} failed RF limits across multiple calibrated stations. "
            f"Route device to Failure Analysis laboratory for X-ray shield audit per {sop}."
        )
    elif cat == "FIXTURE_CONTACT":
        ticket_type = "FIXTURE_INSPECTION_WORK_ORDER"
        target_entity = f"Fixture_{target_station}"
        priority = priority_override or "HIGH"
        title = f"INSPECT {target_entity}: High Contact Variance & Pogo Pin Wear"
        desc = (
            f"Elevated repeatability variance and contact discontinuity detected on {target_station}. "
            f"Perform optical inspection and alcohol swab cleaning per {sop}."
        )
    elif cat == "INSTRUMENT_CALIBRATION":
        ticket_type = "METROLOGY_CALIBRATION_ORDER"
        target_entity = f"Station_{target_station}_Instrumentation"
        priority = priority_override or "CRITICAL"
        title = f"RECALIBRATE {target_entity}: Overdue Calibration Interval"
        desc = (
            f"Station {target_station} has exceeded its certified calibration due date. "
            f"Dispatch metrology calibration team and freeze production runs per {sop}."
        )
    elif cat == "SPEC_OR_REVISION_MISMATCH":
        ticket_type = "ENGINEERING_LIMIT_SYNC"
        target_entity = "Test_Limits_Matrix"
        priority = priority_override or "MEDIUM"
        title = "SYNC LIMITS: Hardware Revision Matrix Mismatch"
        desc = (
            f"Device revision does not match loaded test specification limits table. "
            f"Synchronize production limit matrix per {sop}."
        )
    else:
        ticket_type = "VERIFICATION_SWEEP_DISPATCH"
        target_entity = f"Station_{target_station}"
        priority = priority_override or "HIGH"
        title = f"EXPEDITE {target_entity}: Missing Golden Baseline Sweep"
        desc = (
            f"Investigation package lacks essential golden unit baseline verification runs. "
            f"Automated disposition suspended (status: NEEDS_MORE_DATA). Execute golden verification per {sop}."
        )

    return EvolusTicket(
        ticket_id=ticket_uid,
        ticket_type=ticket_type,
        target_entity=target_entity,
        priority=priority,
        status="DISPATCHED",
        title=title,
        description=desc,
        sop_reference=sop,
        action_items=rep.recommended_actions,
        case_id=case_id,
        run_id=run_id,
        timestamp=timestamp,
        dispatched_by="TestTrace-Guard-v0.1.0",
        dispatch_mode="mock",
    )


def dispatch_evolus_ticket(
    ticket: EvolusTicket,
    evolus_dir: Path = DEFAULT_EVOLUS_DIR,
    base_url: Optional[str] = None,
) -> EvolusTicket:
    """Dispatch ticket to remote Evolus endpoint or persist locally in mock mode."""
    mode = os.getenv("EVOLUS_MODE", "mock").lower()
    evolus_dir.parent.mkdir(parents=True, exist_ok=True)
    evolus_dir.mkdir(parents=True, exist_ok=True)

    if mode == "live" and base_url:
        ticket.dispatch_mode = "live"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(f"{base_url}/api/v1/tickets", json=ticket.model_dump())
                if resp.status_code in [200, 201]:
                    ticket.status = "ACKNOWLEDGED_BY_EVOLUS"
                else:
                    logger.warning("Evolus live endpoint returned %d; storing locally.", resp.status_code)
                    ticket.status = "DISPATCHED_PENDING_ACK"
        except Exception as exc:
            logger.warning("Failed to reach live Evolus endpoint (%s); falling back to local queue.", exc)
            ticket.status = "DISPATCHED_OFFLINE_QUEUED"
    else:
        ticket.dispatch_mode = "mock"
        ticket.status = "DISPATCHED"

    ticket_file = evolus_dir / f"{ticket.ticket_id}_{ticket.ticket_type}.json"
    with open(ticket_file, "w", encoding="utf-8") as f:
        json.dump(ticket.model_dump(), f, indent=2)

    logger.info("Evolus ticket %s persisted to %s", ticket.ticket_id, ticket_file.name)
    return ticket


def list_dispatched_tickets(evolus_dir: Path = DEFAULT_EVOLUS_DIR) -> list[EvolusTicket]:
    """Retrieve all dispatched tickets from the storage directory."""
    if not evolus_dir.exists():
        return []

    tickets: list[EvolusTicket] = []
    for f in sorted(evolus_dir.glob("EVO-*.json"), reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                tickets.append(EvolusTicket.model_validate(data))
        except Exception as exc:
            logger.warning("Error reading ticket file %s: %s", f.name, exc)
    return tickets
