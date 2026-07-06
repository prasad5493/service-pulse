# Everything observability-related in one place: the workspace the logs go
# to, the Application Insights instance the function reports into, and the
# alert that tells a human when checks start failing.

resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${var.prefix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_application_insights" "main" {
  name                = "appi-${var.prefix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "other"
  tags                = var.tags
}

resource "azurerm_monitor_action_group" "oncall" {
  name                = "ag-${var.prefix}-oncall"
  resource_group_name = var.resource_group_name
  short_name          = "oncall"
  tags                = var.tags

  email_receiver {
    name          = "oncall-email"
    email_address = var.alert_email
  }
}

# Fires when the function logs errors — which is exactly what checks.py does
# for every failed health check. Evaluated every 5 minutes over a 10-minute
# window, so a single blip won't page anyone but a real outage will.
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "failed_checks" {
  name                 = "alert-${var.prefix}-failed-checks"
  resource_group_name  = var.resource_group_name
  location             = var.location
  scopes               = [azurerm_application_insights.main.id]
  severity             = 2
  evaluation_frequency = "PT5M"
  window_duration      = "PT10M"
  tags                 = var.tags

  criteria {
    query = <<-KQL
      traces
      | where message has '"event": "health_check"'
      | where severityLevel >= 3
    KQL

    time_aggregation_method = "Count"
    operator                = "GreaterThanOrEqual"
    threshold               = 2
  }

  action {
    action_groups = [azurerm_monitor_action_group.oncall.id]
  }

  description = "Two or more failed health checks in the last 10 minutes."
}
