variable "prefix" {
  description = "Naming prefix shared with the root module."
  type        = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "alert_email" {
  description = "Address that receives alert emails."
  type        = string
  sensitive   = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
