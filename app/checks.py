"""Core health-check logic.

Kept deliberately separate from the Azure Functions entry point so it can be
run locally, put in a container, and unit tested without any cloud plumbing.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

logger = logging.getLogger("service_pulse")

CONFIG_PATH = Path(__file__).parent / "endpoints.json"


@dataclass
class CheckResult:
    name: str
    url: str
    ok: bool
    status_code: int | None
    latency_ms: float | None
    error: str | None = None


def load_endpoints(path: Path = CONFIG_PATH) -> list[dict]:
    """Read the list of endpoints to monitor from the JSON config."""
    with open(path) as f:
        return json.load(f)["endpoints"]


def check_endpoint(endpoint: dict) -> CheckResult:
    """Call one endpoint and record what happened.

    A check passes if the endpoint answers with a 2xx or 3xx status within
    its timeout. Anything else (4xx, 5xx, timeout, DNS failure) is a fail.
    """
    started = time.monotonic()
    try:
        response = requests.get(
            endpoint["url"],
            timeout=endpoint.get("timeout_seconds", 5),
            headers={"User-Agent": "service-pulse/1.0"},
        )
        latency_ms = round((time.monotonic() - started) * 1000, 1)
        return CheckResult(
            name=endpoint["name"],
            url=endpoint["url"],
            ok=response.status_code < 400,
            status_code=response.status_code,
            latency_ms=latency_ms,
        )
    except requests.RequestException as exc:
        latency_ms = round((time.monotonic() - started) * 1000, 1)
        return CheckResult(
            name=endpoint["name"],
            url=endpoint["url"],
            ok=False,
            status_code=None,
            latency_ms=latency_ms,
            error=type(exc).__name__,
        )


def run_all_checks(path: Path = CONFIG_PATH) -> list[CheckResult]:
    """Run every configured check and log each result as structured JSON.

    Azure Functions forwards these log lines to Application Insights, which
    is where the dashboards and alert rules read them from.
    """
    results = [check_endpoint(e) for e in load_endpoints(path)]
    for result in results:
        payload = json.dumps({"event": "health_check", **asdict(result)})
        if result.ok:
            logger.info(payload)
        else:
            logger.error(payload)
    return results


if __name__ == "__main__":
    # Quick local run: python -m checks
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    outcomes = run_all_checks()
    failed = [r for r in outcomes if not r.ok]
    print(f"\n{len(outcomes) - len(failed)}/{len(outcomes)} checks passing")
    raise SystemExit(1 if failed else 0)
