# AGENTS.md

Context file for AI coding assistants working in this repository.

## Project Purpose

Terraform IaC for automating Jamf Pro, Jamf Security Cloud, and Jamf Protect. **This repo is used by organizations as a starting point for production Jamf environments.** Security and correctness are critical.

## Providers

- **jamfpro**: [deploymenttheory/jamfpro](https://registry.terraform.io/providers/deploymenttheory/jamfpro/latest/docs)
- **jsc**: [Jamf-Concepts/jsctfprovider](https://registry.terraform.io/providers/Jamf-Concepts/jsctfprovider/latest/docs)

## Directory Structure

```
├── main.tf              # Root module - all module calls with count conditions
├── variables.tf         # Root variables (credentials, feature flags)
├── providers.tf         # Provider configuration with aliases (jpro, jsc)
├── spec.yml             # Module specification - defines all options
└── modules/
    ├── compliance-*     # Security benchmarks (CIS, STIG, NIST, CMMC)
    ├── configuration-*  # Jamf Pro and JSC service configuration
    ├── endpoint-security-*  # FileVault, CrowdStrike, Defender
    ├── management-*     # Device management, app installers
    ├── network-security-*   # Content filtering, ZTNA, threat defense
    └── onboarder-*      # Bundled parent modules
```

## Security Requirements

### Credentials
- **Never hardcode** credentials in `.tf` files
- All `*_secret`, `*_password` variables must include `sensitive = true`
- Credentials are passed via `terraform.tfvars` (gitignored)

### State Files
- `.tfstate` files contain secrets in plaintext - **never commit**
- Use remote state with encryption for production (S3, Terraform Cloud)

### Provider Versions
- Pin provider versions in `providers.tf` to avoid breaking changes
- Test upgrades in staging before production

## Module Structure

Every module requires:
```
module-name/
├── main.tf          # Resources (start with provider block)
├── variables.tf     # Input variables
└── README.md        # Documentation
```

Optional:
```
└── support_files/
    ├── computer_scripts/           # .sh files
    ├── computer_config_profiles/   # .mobileconfig files
    └── computer_extension_attributes/  # .sh files
```

## Naming Conventions

### Modules
Pattern: `<category>-<platform>-<feature>`
- `compliance-macOS-cis-level-1`
- `endpoint-security-macOS-filevault`
- `management-iOS-configuration-profiles`

### Resources
Pattern: `<type>_<os_version>_<framework>_<descriptor>`
- `category_sonoma_cis_lvl1_benchmarks`
- `script_sequoia_stig_compliance`
- `group_tahoe_cis_lvl1_non_compliant`

### Variables
- Feature flags: `include_<feature>` (boolean)
- Credentials: `<provider>_<credential_type>`
- Always use `sensitive = true` for secrets

## Provider Pattern

All modules use aliased providers:

```hcl
terraform {
  required_providers {
    jamfpro = {
      source                = "deploymenttheory/jamfpro"
      configuration_aliases = [jamfpro.jpro]
    }
  }
}
```

## Resource Creation Order

1. Categories
2. Scripts
3. Extension Attributes
4. Smart Groups
5. Policies
6. Configuration Profiles

Use implicit dependencies (resource references). Add explicit `depends_on` only for cross-provider dependencies.

## Before Making Changes

1. Read the existing module code to understand patterns
2. Check `spec.yml` for related options
3. Follow existing naming conventions exactly
4. Mark sensitive variables appropriately
5. Test with `terraform plan` before applying

## Documentation

**In this repo:**
- [STYLE_GUIDE.md](./STYLE_GUIDE.md) - Naming conventions, patterns, security checklist
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Development workflow, testing requirements
- [MODULE_TEMPLATE.md](./MODULE_TEMPLATE.md) - Templates for new modules
- [testing/README.md](./testing/README.md) - Testing guide

**External:**
- [Terraform Docs](https://developer.hashicorp.com/terraform/docs)
- [jamfpro Provider](https://registry.terraform.io/providers/deploymenttheory/jamfpro/latest/docs)
- [jsc Provider](https://registry.terraform.io/providers/Jamf-Concepts/jsctfprovider/latest/docs)
