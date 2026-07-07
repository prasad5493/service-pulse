"""Sends check results straight to Application Insights over HTTPS.

Normally the Azure Function does this automatically just by using Python's
logging module — Azure wires that up for you. Here, because the checks are
running inside a GitHub Actions job instead of inside Azure, we send the
same shape of event ourselves using Application Insights' plain HTTP
ingestion endpoint. No SDK, no extra dependency beyond `requests`.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone

import requests

from checks import CheckResult


def _parse_connection_string(conn_str: str) -> tuple[str, str]:
    """Pull the instrumentation key and ingestion endpoint out of a
    connection string like:
    'InstrumentationKey=<guid>;IngestionEndpoint=https://...'
    """
    parts = dict(
        item.split("=", 1) for item in conn_str.strip().split(";") if "=" in item
    )
    ikey = parts["InstrumentationKey"]
    endpoint = parts.get("IngestionEndpoint", "https://dc.services.visualstudio.com").rstrip("/")
    return ikey, endpoint


def send_result(result: CheckResult, connection_string: str) -> None:
    """Send one check result to Application Insights as a trace message,
    in the same JSON shape checks.py already logs — so the alert rule
    Terraform created (which scans for '"event": "health_check"' at
    severity >= 3) fires exactly the same way regardless of where the
    check actually ran.
    """
    ikey, endpoint = _parse_connection_string(connection_string)

    message = json.dumps(
        {
            "event": "health_check",
            "name": result.name,
            "url": result.url,
            "ok": result.ok,
            "status_code": result.status_code,
            "latency_ms": result.latency_ms,
            "error": result.error,
        }
    )

    payload = {
        "name": "Microsoft.ApplicationInsights.Message",
        "time": datetime.now(timezone.utc).isoformat(),
        "iKey": ikey,
        "tags": {"ai.cloud.role": "github-actions-monitor"},
        "data": {
            "baseType": "MessageData",
            "baseData": {
                "ver": 2,
                "message": message,
                "severityLevel": 1 if result.ok else 3,  # 1=Information, 3=Error
            },
        },
    }

    response = requests.post(f"{endpoint}/v2/track", json=payload, timeout=10)
    response.raise_for_status()


def send_all(results: list[CheckResult]) -> None:
    connection_string = os.environ.get("APPINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        print("APPINSIGHTS_CONNECTION_STRING not set, skipping upload.")
        return

    for result in results:
        try:
            send_result(result, connection_string)
        except requests.RequestException as exc:
            # Never let a telemetry hiccup fail the whole run.
            print(f"Could not send result for {result.name}: {exc}")
        time.sleep(0.2)  # be gentle with the ingestion endpoint


if __name__ == "__main__":
    from checks import run_all_checks

    outcomes = run_all_checks()
    send_all(outcomes)
    failed = [r for r in outcomes if not r.ok]
    print(f"\n{len(outcomes) - len(failed)}/{len(outcomes)} checks passing")

    # Optional Salesforce case creation, same as the Function App does.
    if failed:
        from notify import open_case_for_failure

        for failure in failed:
            try:
                open_case_for_failure(failure)
            except Exception as exc:  # noqa: BLE001 - never break the run
                print(f"Could not open Salesforce case for {failure.name}: {exc}")

    raise SystemExit(1 if failed else 0)
