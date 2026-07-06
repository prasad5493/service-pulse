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

locals {
  # One place to build names and tags, so every resource is consistent.
  prefix = "${var.project}-${var.environment}"

  tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
  }
}
