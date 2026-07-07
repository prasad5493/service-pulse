variable "project" {
  description = "Short name used as a prefix on every resource."
  type        = string
  default     = "svcpulse"
}

variable "location" {
  description = "Azure region to deploy into."
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "alert_email" {
  description = "Address that receives alert emails when checks fail."
  type        = string
  sensitive   = true
}

variable "enable_function_app" {
  description = "Create the Azure Function App and its Service Plan. Leave false until Azure has approved App Service quota for this subscription/region; the checks run via a GitHub Actions schedule in the meantime."
  type        = bool
  default     = false
}

locals {
  # One place to build names and tags, so every resource is consistent.
  prefix = "${var.project}-${var.environment}"

  tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
  }
}
