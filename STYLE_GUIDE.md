# Style Guide

Conventions for contributing to terraform-jamf-platform.

## Module Naming

**Pattern:** `<category>-<platform>-<feature>`

| Category | Purpose | Examples |
|----------|---------|----------|
| `compliance-` | Security benchmarks | `compliance-macOS-cis-level-1` |
| `configuration-` | Service configuration | `configuration-jamf-pro-categories` |
| `endpoint-security-` | Endpoint protection | `endpoint-security-macOS-filevault` |
| `management-` | Device/app management | `management-iOS-configuration-profiles` |
| `network-security-` | Network policies | `network-security-jamf-pro-content-filtering` |
| `onboarder-` | Bundled modules | `onboarder-management-macOS` |

**Platform identifiers:** `macOS`, `iOS`, `jamf-pro`, `jamf-security-cloud`

## Resource Naming

**Pattern:** `<type>_<context>_<descriptor>`

### Categories
```hcl
resource "jamfpro_category" "category_sonoma_cis_lvl1_benchmarks" {
  name     = "Sonoma - CIS Level 1 Benchmarks"
  priority = 9
}
```

### Scripts
```hcl
resource "jamfpro_script" "script_sequoia_stig_compliance" {
  name            = "Sequoia - DISA STIG Compliance"
  script_contents = file("${path.module}/support_files/computer_scripts/sequoia_stig_compliance.sh")
  category_id     = jamfpro_category.category_sequoia_stig_benchmarks.id
}
```

### Smart Groups
```hcl
resource "jamfpro_smart_computer_group" "group_sonoma_cis_lvl1_non_compliant" {
  name = "CIS Level 1 - Sonoma - Non Compliant Computers"
  # ...
}
```

### Extension Attributes
```hcl
resource "jamfpro_computer_extension_attribute" "ea_cis_lvl1_failed_count" {
  name = "CIS Level 1 - Failed Results Count"
  # ...
}
```

### Policies
```hcl
resource "jamfpro_policy" "policy_sonoma_cis_lvl1_audit" {
  name = "CIS Level 1 - Audit (Sonoma)"
  # ...
}
```

## Variable Naming

### Feature Flags
```hcl
variable "include_mac_cis_lvl1_benchmark" {
  description = "Enable CIS Level 1 benchmark for macOS"
  type        = bool
  default     = false
}
```

### Credentials (always mark sensitive)
```hcl
variable "jamfpro_client_secret" {
  description = "Jamf Pro client secret for API authentication"
  type        = string
  sensitive   = true
}
```

### Provider URLs
```hcl
variable "jamfpro_instance_url" {
  description = "Jamf Pro instance URL (must start with https://)"
  type        = string
}
```

## File Structure

### Required Files
Every module must have:

**main.tf**
```hcl
terraform {
  required_providers {
    jamfpro = {
      source                = "deploymenttheory/jamfpro"
      configuration_aliases = [jamfpro.jpro]
    }
  }
}

# Resources follow...
```

**variables.tf**
```hcl
variable "jamfpro_instance_url" {
  description = "Jamf Pro Instance URL"
  type        = string
}

variable "jamfpro_client_id" {
  description = "Jamf Pro Client ID"
  type        = string
}

variable "jamfpro_client_secret" {
  description = "Jamf Pro Client Secret"
  type        = string
  sensitive   = true
}
```

**README.md**
```markdown
# Module Name

Brief description of what this module configures.

## Usage

Example module call.

## Requirements

- Jamf Pro API credentials with appropriate permissions
```

### Support Files

When modules need external files:

```
support_files/
├── computer_scripts/
│   └── <os_version>_<framework>_<action>.sh
├── computer_config_profiles/
│   └── <OsVersion>_<framework>_<level>-<domain>.mobileconfig
├── computer_extension_attributes/
│   └── <context>-<MetricName>.sh
└── mobile_configuration_profiles/
    └── <platform><version>_<framework>-<domain>.mobileconfig
```

**Examples from codebase:**
- `sonoma_cis_lvl1_compliance.sh`
- `Tahoe_cis_lvl1-MCX.mobileconfig`
- `compliance-FailedResultsCount.sh`
- `iOS17_cis_lvl1_enterprise-applicationaccess.mobileconfig`

**File references:**
```hcl
script_contents = file("${path.module}/support_files/computer_scripts/sonoma_cis_lvl1_compliance.sh")
```

## Resource Creation Order

Create resources in this order to ensure proper dependency resolution:

1. **Categories** - Organizational containers
2. **Scripts** - Reference category IDs
3. **Extension Attributes** - Independent, used by smart groups
4. **Smart Groups** - Reference extension attribute names in criteria
5. **Policies** - Reference scripts and smart groups
6. **Configuration Profiles** - Scoped to smart groups

### Dependencies

**Implicit (preferred):**
```hcl
resource "jamfpro_script" "script" {
  category_id = jamfpro_category.category.id  # Creates implicit dependency
}
```

**Explicit (when required):**
```hcl
resource "jamfpro_macos_configuration_profile_plist" "profile" {
  depends_on = [jsc_ap.content_filtering_only]  # Cross-provider dependency
}
```

## Conditional Module Inclusion

In `main.tf`, use count for feature flags:

```hcl
module "compliance-macOS-cis-level-1" {
  count  = var.include_mac_cis_lvl1_benchmark ? 1 : 0
  source = "./modules/compliance-macOS-cis-level-1"

  jamfpro_instance_url  = var.jamfpro_instance_url
  jamfpro_client_id     = var.jamfpro_client_id
  jamfpro_client_secret = var.jamfpro_client_secret

  providers = {
    jamfpro.jpro = jamfpro.jpro
  }
}
```

## Security Checklist

Before submitting a PR:

- [ ] No hardcoded credentials or secrets
- [ ] All `*_secret`, `*_password` variables have `sensitive = true`
- [ ] No `.tfstate` files committed
- [ ] No `terraform.tfvars` committed
- [ ] Provider versions pinned appropriately
- [ ] `terraform fmt -recursive` passes
- [ ] `terraform validate` passes
- [ ] Module tested with `terraform plan`

## Terraform and Provider Versions

### Terraform Version Constraint

Root `providers.tf` specifies provider versions:

```hcl
terraform {
  required_providers {
    jamfpro = {
      source  = "deploymenttheory/jamfpro"
      version = "0.30.0"
    }
    jsc = {
      source  = "Jamf-Concepts/jsctfprovider"
      version = ">= 0.0.23"
    }
  }
}
```

### Provider Version Constraints

| Constraint | Syntax | Use Case |
|------------|--------|----------|
| Exact | `"0.30.0"` | Reproducibility, prevents unexpected changes |
| Minimum | `">= 0.0.23"` | Allows newer versions with fixes |

**This repo uses:** Exact versioning for jamfpro provider (stability), minimum versioning for jsc provider.

Reference: [Terraform Version Constraints](https://developer.hashicorp.com/terraform/language/expressions/version-constraints)

## Outputs

### When to Use outputs.tf

Create a separate `outputs.tf` file when a module exposes values for:
- Parent module consumption
- Cross-module references
- Operational visibility (IDs, URLs, status)

### Output Pattern
```hcl
# outputs.tf
output "category_id" {
  description = "ID of the created category"
  value       = jamfpro_category.category.id
}

output "smart_group_ids" {
  description = "Map of smart group names to IDs"
  value       = { for k, v in jamfpro_smart_computer_group.groups : k => v.id }
}

output "profile_deployment_status" {
  description = "Status code from profile deployment"
  value       = data.http.profile.status_code
  sensitive   = false
}
```

### Output Naming
- Use descriptive nouns with underscores
- Include resource type context: `category_id`, `script_name`, `group_ids`
- Mark sensitive outputs: `sensitive = true`

Reference: [Terraform Outputs](https://developer.hashicorp.com/terraform/language/values/outputs)

## Locals Organization

### When to Use locals.tf

Create a separate `locals.tf` file when a module has:
- 3 or more local values
- Complex computed values
- File path mappings for `for_each`

### Local Value Patterns

**String Normalization:**
```hcl
# locals.tf
locals {
  # Normalize URL input
  _url_lower   = lower(trimspace(var.instance_url))
  _url_no_proto = replace(replace(local._url_lower, "https://", ""), "http://", "")
  instance_host = split("/", local._url_no_proto)[0]
}
```

**File Mappings for for_each:**
```hcl
# locals.tf
locals {
  sonoma_profiles = {
    "Application Access" = "${path.module}/support_files/computer_config_profiles/sonoma-applicationaccess.mobileconfig"
    "Security Firewall"  = "${path.module}/support_files/computer_config_profiles/sonoma-security.firewall.mobileconfig"
  }
}

# main.tf
resource "jamfpro_macos_configuration_profile_plist" "sonoma" {
  for_each = local.sonoma_profiles
  name     = "Sonoma - ${each.key}"
  payloads = file(each.value)
}
```

**Naming Convention:**
- Prefix intermediate values with underscore: `_url_lower`, `_temp_value`
- Use descriptive names for final values: `instance_host`, `profile_dict`

Reference: [Terraform Local Values](https://developer.hashicorp.com/terraform/language/values/locals)

## Lifecycle Blocks

Use lifecycle blocks to control resource behavior during create, update, and destroy operations.

### prevent_destroy

Protect critical resources from accidental deletion:

```hcl
resource "jamfpro_category" "production" {
  name = "Production - Critical"

  lifecycle {
    prevent_destroy = true
  }
}
```

### ignore_changes

Prevent Terraform from reverting external changes:

```hcl
resource "jamfpro_smart_computer_group" "dynamic" {
  name = "Dynamic Group"

  lifecycle {
    ignore_changes = all  # Allow all manual updates
  }
}
```

### When to Use

| Block | Use Case |
|-------|----------|
| `prevent_destroy` | Production categories, critical policies |
| `ignore_changes` | Resources modified outside Terraform |
| `create_before_destroy` | Zero-downtime replacements |

Reference: [Terraform Lifecycle](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle)

## Compliance Module Pattern

For security benchmarks (CIS, STIG, NIST, CMMC):

1. **Categories** per OS version (Sonoma, Sequoia, Tahoe)
2. **Scripts** per OS version for compliance checks
3. **Extension Attributes** (3 per benchmark):
   - `*_failed_count` - Number of failed controls
   - `*_failed_list` - List of failed control IDs
   - `*_version` - Benchmark version applied
4. **Smart Groups**:
   - `*_computers` - All computers for this OS
   - `*_non_compliant` - Computers with failed_count > 0
5. **Policies**:
   - `*_audit` - Check compliance status
   - `*_remediation` - Fix non-compliant settings
6. **Configuration Profiles** - Enforce settings via MDM

## spec.yml Updates

When adding new modules or options, update `spec.yml`:

```yaml
options:
  - key: include_new_feature
    type: <boolean>
    presence: optional
    module_name: module.new-module-name
    required_provider: jpro
    category: Category Name
    display_name: Feature Display Name
    display_desc: Description for the Onboarder UI
```

## References

- [Terraform Language Documentation](https://developer.hashicorp.com/terraform/language)
- [Terraform Best Practices](https://developer.hashicorp.com/terraform/cloud-docs/recommended-practices)
- [jamfpro Provider Docs](https://registry.terraform.io/providers/deploymenttheory/jamfpro/latest/docs)
- [jsc Provider Docs](https://registry.terraform.io/providers/Jamf-Concepts/jsctfprovider/latest/docs)
