resource "azurerm_resource_group" "main" {
  name     = "rg-${local.prefix}"
  location = var.location
  tags     = local.tags
}

# Storage the Functions runtime needs for its own state (timers, leases).
resource "azurerm_storage_account" "func" {
  name                            = replace("st${local.prefix}", "-", "")
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = local.tags
}

# Consumption plan: we only pay while the checks are actually running,
# which for a 5-minute timer is close to nothing.
resource "azurerm_service_plan" "main" {
  name                = "plan-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "Y1"
  tags                = local.tags
}

resource "azurerm_linux_function_app" "main" {
  name                = "func-${local.prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  storage_account_name       = azurerm_storage_account.func.name
  storage_account_access_key = azurerm_storage_account.func.primary_access_key
  https_only                 = true

  # Managed identity instead of stored credentials wherever possible.
  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.11"
    }
    application_insights_connection_string = module.monitoring.app_insights_connection_string
    minimum_tls_version                    = "1.2"
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME = "python"
    # Salesforce credentials are injected by the deploy pipeline only when
    # the integration is switched on; they are never committed here.
  }

  tags = local.tags
}

# All observability concerns live in one reusable module.
module "monitoring" {
  source = "./modules/monitoring"

  prefix              = local.prefix
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  alert_email         = var.alert_email
  tags                = local.tags
}
