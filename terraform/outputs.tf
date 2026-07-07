output "function_app_name" {
  description = "Name of the Function App, used by the deploy workflow. Empty when enable_function_app is false."
  value       = var.enable_function_app ? azurerm_linux_function_app.main[0].name : ""
}

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "app_insights_name" {
  description = "Where the check results and dashboards live."
  value       = module.monitoring.app_insights_name
}

output "app_insights_connection_string" {
  description = "Used by the GitHub Actions monitor workflow to send check results directly, when the Function App is disabled."
  value       = module.monitoring.app_insights_connection_string
  sensitive   = true
}
