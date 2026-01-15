variable "jamfpro_instance_url" {
  description = "Jamf Pro instance URL (must start with https://)"
  type        = string
}

variable "jamfpro_client_id" {
  description = "Jamf Pro Client ID for API authentication"
  type        = string
}

variable "jamfpro_client_secret" {
  description = "Jamf Pro Client Secret for API authentication"
  type        = string
  sensitive   = true
}

variable "random_string" {
  description = "Optional suffix for resource names to ensure uniqueness"
  type        = string
  default     = ""
}

## LAPS Configuration Variables

variable "laps_auto_deploy_enabled" {
  description = "When enabled, all appropriate computers will have the SetAutoAdminPassword command sent automatically"
  type        = bool
  default     = false
}

variable "laps_password_rotation_time_seconds" {
  description = "Time in seconds before the local admin password is rotated after being viewed (default: 1 hour)"
  type        = number
  default     = 3600
}

variable "laps_auto_rotate_enabled" {
  description = "When enabled, passwords will automatically expire and rotate after the configured expiration time"
  type        = bool
  default     = false
}

variable "laps_auto_rotate_expiration_time_seconds" {
  description = "Time in seconds before automatic password rotation if never viewed (default: 90 days)"
  type        = number
  default     = 7776000
}
