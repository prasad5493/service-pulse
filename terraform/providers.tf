terraform {
  required_version = ">= 1.7"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # Remote state in Azure Storage, created once by scripts/bootstrap.sh.
  # Keeping state out of the repo and out of laptops.
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "stservicepulsetfstate"
    container_name       = "tfstate"
    key                  = "service-pulse.tfstate"
    use_oidc             = true
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  use_oidc = true
}
