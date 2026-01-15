# endpoint-security-macOS-laps

Configures Local Administrator Password Solution (LAPS) settings in Jamf Pro for automatic management and rotation of local admin passwords on macOS devices.

## Resources Created

- **Local Admin Password Settings**: Singleton configuration for LAPS behavior across all managed Macs

## Usage

```hcl
module "endpoint-security-macOS-laps" {
  source = "./modules/endpoint-security-macOS-laps"

  jamfpro_instance_url  = var.jamfpro_instance_url
  jamfpro_client_id     = var.jamfpro_client_id
  jamfpro_client_secret = var.jamfpro_client_secret

  # LAPS Configuration
  laps_auto_deploy_enabled                 = true
  laps_password_rotation_time_seconds      = 3600   # 1 hour after viewing
  laps_auto_rotate_enabled                 = true
  laps_auto_rotate_expiration_time_seconds = 7776000 # 90 days if never viewed

  providers = {
    jamfpro.jpro = jamfpro.jpro
  }
}
```

## Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `laps_auto_deploy_enabled` | bool | `false` | Auto-send SetAutoAdminPassword to computers |
| `laps_password_rotation_time_seconds` | number | `3600` | Rotate password X seconds after viewing |
| `laps_auto_rotate_enabled` | bool | `false` | Enable automatic rotation |
| `laps_auto_rotate_expiration_time_seconds` | number | `7776000` | Auto-rotate after X seconds if never viewed |

## Requirements

- Jamf Pro 10.36 or later (LAPS support)
- API credentials with permission to manage Local Admin Password settings
- Computers must be enrolled with a management account for LAPS to function

## Notes

- This is a singleton resource - only one LAPS configuration exists per Jamf Pro instance
- LAPS requires macOS 10.15 (Catalina) or later on managed devices
- The local admin account must exist on the computer for password rotation to work
- Passwords are stored securely in Jamf Pro and can be viewed by administrators with appropriate permissions
