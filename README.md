# Service Pulse

A small, practical uptime monitor that runs on Azure. Every five minutes it checks a list of web endpoints, records how they respond, and raises an alert (and optionally a Salesforce case) when something looks unhealthy.

I built this to practise the day-to-day work of a platform team in one small repo: infrastructure as code, a CI/CD pipeline, observability, and a bit of automation glue — without any of it being over-engineered.

**Live docs site:** hosted with GitHub Pages from the `docs/` folder.

---

## What it does

1. A Python function runs in Azure on a timer (every 5 minutes).
2. It reads a list of endpoints from `app/endpoints.json` and calls each one.
3. Each result (status code, latency, pass/fail) is logged as structured JSON, which lands in Application Insights automatically.
4. An Azure Monitor alert fires if checks start failing, and emails the on-call address.
5. Optionally, a failed check can open a Case in Salesforce so the issue is tracked somewhere people actually look. This is switched off unless you provide Salesforce credentials — the monitor works fine without it.

## Why it's built this way

- **Terraform for everything.** All Azure resources live in `terraform/`. The monitoring pieces (Log Analytics, Application Insights, alert rules) sit in their own small module so they can be reused, and to keep the root config short and readable.
- **GitHub Actions for CI/CD.** Pull requests run linting, unit tests, `terraform validate` and a security scan. Merges to `main` deploy the infrastructure and the function code. The pipeline logs into Azure with OIDC (federated credentials), so there are no long-lived cloud secrets stored in GitHub.
- **Observability from day one.** Logs are structured, latency is recorded per check, and there's an alert rule rather than "someone will notice eventually".
- **Small and honest.** No Kubernetes, no queues, no framework. A timer, some HTTP calls, and good habits around them.

## Architecture

```
GitHub Actions ──(OIDC)──> Azure
     │
     ├── terraform apply ──> Resource Group
     │                        ├── Storage Account (function state)
     │                        ├── App Service Plan (consumption)
     │                        ├── Function App (Python)
     │                        └── monitoring module
     │                             ├── Log Analytics Workspace
     │                             ├── Application Insights
     │                             ├── Action Group (email)
     │                             └── Alert rule (failed checks)
     │
     └── deploy function code ──> Function App
                                     │ every 5 min
                                     ▼
                              checks endpoints ──> logs to App Insights
                                     │
                                     └─ on failure ──> Salesforce Case (optional)
```

## Project layout

```
app/          Python function code and endpoint config
tests/        Unit tests (pytest)
terraform/    Infrastructure as code, with a reusable monitoring module
scripts/      One-off helper scripts (bootstrap the Terraform state storage)
docs/         The GitHub Pages site
.github/      CI and deploy workflows
Dockerfile    Run the checks locally in a container
```

## Running it locally

You don't need Azure to try the checks:

```bash
cd app
pip install -r requirements.txt
python -m checks              # runs the checks once and prints the results
```

Or in a container, so the environment is the same everywhere:

```bash
docker build -t service-pulse .
docker run --rm service-pulse
```

Run the tests:

```bash
pip install -r app/requirements.txt pytest ruff
pytest
```

## Deploying to Azure

One-time setup:

1. Create the storage account that holds Terraform state:

   ```bash
   ./scripts/bootstrap.sh <subscription-id> uksouth
   ```

2. Create an Entra ID app registration with federated credentials for this repo, and give it Contributor on the subscription (or a tighter scope if you prefer). Add these repository secrets in GitHub:

   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
   - `ALERT_EMAIL` — where alert emails should go

3. (Optional) For the Salesforce integration, also add:

   - `SF_USERNAME`, `SF_PASSWORD`, `SF_TOKEN`

   If these are missing the function simply skips the Salesforce step.

After that, every merge to `main` runs `terraform apply` and deploys the function.

## Changing what gets monitored

Edit `app/endpoints.json`. Each entry is a name, a URL, and a timeout. That's it — commit the change and the pipeline ships it.

## Things I'd add next

- Debounce Salesforce cases (only open one after N consecutive failures) using a small blob for state.
- Publish a proper SLO: e.g. "99% of checks complete in under 2 seconds", measured from the latency we already record.
- A GitOps-style promotion flow with a separate staging environment.
