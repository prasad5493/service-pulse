"""Optional Salesforce integration.

When a check fails, we can open a Case in Salesforce so the outage is
tracked somewhere the wider team already works. This is entirely optional:
if the SF_* environment variables aren't set, we log that we're skipping it
and move on. The monitor never depends on Salesforce being available.
"""

import logging
import os

from checks import CheckResult

logger = logging.getLogger("service_pulse")


def salesforce_enabled() -> bool:
    return all(os.environ.get(k) for k in ("SF_USERNAME", "SF_PASSWORD", "SF_TOKEN"))


def open_case_for_failure(result: CheckResult) -> str | None:
    """Open a Salesforce Case describing the failed check.

    Returns the new Case id, or None if Salesforce isn't configured.
    Imports simple_salesforce lazily so the package is only needed
    when the integration is actually switched on.
    """
    if not salesforce_enabled():
        logger.info("Salesforce not configured, skipping case for %s", result.name)
        return None

    from simple_salesforce import Salesforce

    sf = Salesforce(
        username=os.environ["SF_USERNAME"],
        password=os.environ["SF_PASSWORD"],
        security_token=os.environ["SF_TOKEN"],
    )

    detail = f"HTTP {result.status_code}" if result.status_code else result.error
    case = sf.Case.create(
        {
            "Subject": f"[Service Pulse] {result.name} is failing health checks",
            "Description": (
                f"Endpoint: {result.url}\n"
                f"Result: {detail}\n"
                f"Latency: {result.latency_ms} ms\n\n"
                "Raised automatically by the Service Pulse monitor."
            ),
            "Origin": "Web",
            "Priority": "High",
        }
    )
    case_id = case.get("id")
    logger.info("Opened Salesforce case %s for %s", case_id, result.name)
    return case_id
