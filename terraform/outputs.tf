output "function_app_name" {
  description = "Name of the Function App, used by the deploy workflow."
  value       = azurerm_linux_function_app.main.name
}

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "app_insights_name" {
  description = "Where the check results and dashboards live."
  value       = module.monitoring.app_insights_name
}
