## Provider requirements
terraform {
  required_providers {
    jamfpro = {
      source                = "deploymenttheory/jamfpro"
      configuration_aliases = [jamfpro.jpro]
    }
  }
}

## Local Admin Password Settings (LAPS)
resource "jamfpro_local_admin_password_settings" "laps_settings" {
  auto_deploy_enabled                 = var.laps_auto_deploy_enabled
  password_rotation_time_seconds      = var.laps_password_rotation_time_seconds
  auto_rotate_enabled                 = var.laps_auto_rotate_enabled
  auto_rotate_expiration_time_seconds = var.laps_auto_rotate_expiration_time_seconds
}
