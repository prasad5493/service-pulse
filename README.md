# Service Pulse

A small uptime monitor. It checks a list of websites on a schedule, records how each one responds, and sends an email if something breaks. It can optionally open a Salesforce case for failures too.

I built this to practise the kind of small, everyday platform work that usually gets talked about but rarely gets built end to end: infrastructure as code, a CI/CD pipeline, and proper alerting, in one repo that doesn't take a week to understand.

**Docs site:** hosted with GitHub Pages from the `docs/` folder.

## What it does

- Reads a list of endpoints from `app/endpoints.json`
- Checks each one — records the status code, response time, and pass/fail
- Sends the results to Azure Application Insights
- If two or more checks fail within 10 minutes, an alert email goes out
- Optionally opens a Salesforce case on failure, if credentials are configured — otherwise this step is just skipped

## How the checks run

There are two ways to run the checks, controlled by one flag:

- **GitHub Actions schedule** (default) — a workflow runs every 15 minutes, checks each endpoint, and sends the results to Application Insights.
- **Azure Function** — set `enable_function_app = true` in `terraform/variables.tf` to have Terraform provision a Function App instead, which runs the same checks on its own 5-minute timer inside Azure.

Both paths use the same checking logic in `app/checks.py` and report to the same Application Insights instance, so the alerting and dashboards work identically either way.

## Project layout

```
app/          The checking logic, endpoint config, and the two ways it can run
tests/        Unit tests (pytest)
terraform/    Infrastructure as code, with a small reusable monitoring module
scripts/      One-off setup script for the Terraform state storage
docs/         The GitHub Pages site
.github/      CI, deploy, and the scheduled monitor workflow
Dockerfile    Run the checks locally in a container
```

## Running it locally

```bash
cd app
pip install -r requirements.txt
python -m checks
```

Or in a container:

```bash
docker build -t service-pulse .
docker run --rm service-pulse
```

Run the tests:

```bash
pip install -r app/requirements.txt pytest ruff
pytest
```

## Deploying

1. Create the Terraform state storage (one-time setup):
   ```bash
   ./scripts/bootstrap.sh <subscription-id> eastus
   ```
2. Set up an Azure app registration with federated credentials for this repo, and add these as GitHub repository secrets:
   - `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
   - `ALERT_EMAIL` — where failure alerts should go
   - `APPINSIGHTS_CONNECTION_STRING` — from the Application Insights resource, once created, so the GitHub Actions monitor can send it results
   - Optional: `SF_USERNAME`, `SF_PASSWORD`, `SF_TOKEN` for the Salesforce integration
3. Go to the **Actions** tab and run the **Deploy** workflow manually. Nothing deploys automatically on push — that's deliberate, so changes to real cloud infrastructure only happen when someone means for them to.
4. Run the **Scheduled monitor** workflow once to kick things off. After that it repeats on its own every 15 minutes.

## Changing what gets monitored

Edit `app/endpoints.json` — a name, a URL, and a timeout per entry. Commit it, and the next scheduled run picks it up.

## What I'd add next

- Only open one Salesforce case per outage, instead of one per failed check
- A proper SLO — e.g. 99% of checks under 2 seconds — measured from the latency already being recorded
- A staging environment with its own GitOps-style promotion flow
