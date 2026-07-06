"""Azure Functions entry point.

One timer-triggered function that runs the health checks every five minutes.
All the interesting logic lives in checks.py and notify.py — this file is
just the glue between our code and the Functions runtime.
"""

import logging

import azure.functions as func

from checks import run_all_checks
from notify import open_case_for_failure

app = func.FunctionApp()

logger = logging.getLogger("service_pulse")


@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
def run_health_checks(timer: func.TimerRequest) -> None:
    results = run_all_checks()
    failures = [r for r in results if not r.ok]

    logger.info(
        "Run complete: %d/%d checks passing", len(results) - len(failures), len(results)
    )

    for failure in failures:
        try:
            open_case_for_failure(failure)
        except Exception:  # a Salesforce hiccup must never break the monitor
            logger.exception("Could not open Salesforce case for %s", failure.name)
