# Module Template

Templates for creating new modules in terraform-jamf-platform.

## Quick Start

```bash
# Create module directory
mkdir -p modules/<category>-<platform>-<feature>

# Create required files
touch modules/<category>-<platform>-<feature>/main.tf
touch modules/<category>-<platform>-<feature>/variables.tf
touch modules/<category>-<platform>-<feature>/README.md
```

## Required Files

### main.tf

```hcl
## Provider requirements
terraform {
  required_providers {
    jamfpro = {
      source                = "deploymenttheory/jamfpro"
      configuration_aliases = [jamfpro.jpro]
    }
  }
}

## Categories
resource "jamfpro_category" "category_<name>" {
  name     = "<Display Name>"
  priority = 9
}

## Scripts (if needed)
resource "jamfpro_script" "script_<name>" {
  name            = "<Script Display Name>"
  priority        = "AFTER"
  script_contents = file("${path.module}/support_files/computer_scripts/<script_name>.sh")
  category_id     = jamfpro_category.category_<name>.id
  info            = "Description of what this script does"
}

## Smart Groups (if needed)
resource "jamfpro_smart_computer_group" "group_<name>" {
  name = "<Group Display Name>"

  criteria {
    name        = "<Criteria Name>"
    priority    = 0
    and_or      = "and"
    search_type = "is"
    value       = "<value>"
  }
}

## Policies (if needed)
resource "jamfpro_policy" "policy_<name>" {
  name            = "<Policy Display Name>"
  enabled         = true
  trigger_checkin = true
  frequency       = "Once per computer"
  category_id     = jamfpro_category.category_<name>.id

  scope {
    all_computers      = false
    computer_group_ids = [jamfpro_smart_computer_group.group_<name>.id]
  }

  payloads {
    scripts {
      id       = jamfpro_script.script_<name>.id
      priority = "AFTER"
    }

    maintenance {
      recon = true
    }
  }
}

## Configuration Profiles (if needed)
resource "jamfpro_macos_configuration_profile_plist" "profile_<name>" {
  name                = "<Profile Display Name>"
  description         = "Description for end users"
  level               = "System"
  category_id         = jamfpro_category.category_<name>.id
  distribution_method = "Install Automatically"
  redeploy_on_update  = "Newly Assigned"
  payload_validate    = false
  user_removable      = false

  payloads = file("${path.module}/support_files/computer_config_profiles/<profile>.mobileconfig")

  scope {
    all_computers      = false
    computer_group_ids = [jamfpro_smart_computer_group.group_<name>.id]
  }
}
```

### variables.tf

```hcl
variable "jamfpro_instance_url" {
  description = "Jamf Pro instance URL (must start with https://)"
  type        = string

  validation {
    condition     = can(regex("^https://", var.jamfpro_instance_url))
    error_message = "jamfpro_instance_url must start with 'https://'."
  }
}

variable "jamfpro_client_id" {
  description = "Jamf Pro Client ID for API authentication"
  type        = string

  validation {
    condition     = length(var.jamfpro_client_id) > 0
    error_message = "jamfpro_client_id cannot be empty."
  }
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

# Add module-specific variables below
# variable "example_setting" {
#   description = "Description of what this setting does"
#   type        = string
#   default     = "default_value"
# }
```

### README.md

```markdown
# <Module Name>

Brief description of what this module configures in Jamf Pro.

## Resources Created

- **Categories**: List categories created
- **Scripts**: List scripts created (if any)
- **Smart Groups**: List smart groups created (if any)
- **Policies**: List policies created (if any)
- **Configuration Profiles**: List profiles created (if any)

## Usage

```hcl
module "<module-name>" {
  source = "./modules/<module-name>"

  jamfpro_instance_url  = var.jamfpro_instance_url
  jamfpro_client_id     = var.jamfpro_client_id
  jamfpro_client_secret = var.jamfpro_client_secret

  providers = {
    jamfpro.jpro = jamfpro.jpro
  }
}
```

## Requirements

- Jamf Pro API credentials with appropriate permissions
- List any specific Jamf Pro configuration requirements

## Notes

- Any important notes about scoping, manual steps, or configuration
- Smart Groups are pre-configured with placeholder criteria - modify as needed
```

## Optional Files

### outputs.tf (if module exposes values)

```hcl
output "category_id" {
  description = "ID of the created category"
  value       = jamfpro_category.category_<name>.id
}

output "smart_group_id" {
  description = "ID of the created smart group"
  value       = jamfpro_smart_computer_group.group_<name>.id
}

output "policy_id" {
  description = "ID of the created policy"
  value       = jamfpro_policy.policy_<name>.id
}
```

### locals.tf (if module has 3+ local values)

```hcl
locals {
  # String normalization
  _url_normalized = lower(trimspace(var.some_url))

  # File mappings for for_each
  profile_files = {
    "Profile Name 1" = "${path.module}/support_files/computer_config_profiles/profile1.mobileconfig"
    "Profile Name 2" = "${path.module}/support_files/computer_config_profiles/profile2.mobileconfig"
  }

  # Computed values
  category_name = "Category - ${var.environment}"
}
```

## Support Files Structure

```
support_files/
├── computer_scripts/
│   └── <script_name>.sh
├── computer_config_profiles/
│   └── <profile_name>.mobileconfig
├── computer_extension_attributes/
│   └── <ea_name>.sh
└── mobile_configuration_profiles/
    └── <ios_profile_name>.mobileconfig
```

## Checklist for New Modules

- [ ] Created `main.tf` with provider block
- [ ] Created `variables.tf` with required variables
- [ ] Created `README.md` with usage instructions
- [ ] Added validation blocks to constrained variables
- [ ] Marked sensitive variables with `sensitive = true`
- [ ] Created support_files/ if needed
- [ ] Updated `spec.yml` with new option
- [ ] Added module call to root `main.tf`
- [ ] Created example in `/examples/`
- [ ] Tested with `terraform plan`
- [ ] Tested with `terraform apply`
