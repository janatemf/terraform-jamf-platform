# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**See also:** [AGENTS.md](./AGENTS.md) (agent-agnostic context), [STYLE_GUIDE.md](./STYLE_GUIDE.md) (detailed conventions), [CONTRIBUTING.md](./CONTRIBUTING.md) (development workflow)

## Project Overview

Terraform Infrastructure as Code for automating the Jamf ecosystem. **This repo is used by organizations as a starting point for production Jamf environments - security and correctness are critical.**
- **Jamf Pro** - Device management
- **Jamf Security Cloud (JSC/RADAR)** - Network security & threat defense
- **Jamf Protect** - Endpoint security

Uses community Terraform providers: [jamfpro](https://registry.terraform.io/providers/deploymenttheory/jamfpro/latest) and [jsc](https://registry.terraform.io/providers/Jamf-Concepts/jsctfprovider/latest).

## Commands

```bash
# Initialize providers (run before first apply)
terraform init -upgrade

# Format check (must pass CI)
terraform fmt -check -recursive

# Auto-format files
terraform fmt -recursive

# Validate configuration
terraform validate

# Plan changes
terraform plan

# Apply with reduced parallelism (required for API stability)
export TF_CLI_ARGS_apply="-parallelism=1"
terraform apply
```

## Architecture

### Module Categories (in `/modules/`)

| Category | Prefix | Purpose |
|----------|--------|---------|
| Onboarder | `onboarder-*` | Bundled parent modules (all, macOS, mobile, app-installers) |
| Compliance | `compliance-*` | Security benchmarks (CIS, DISA STIG, CMMC, NIST 800-171) |
| Configuration | `configuration-*` | Jamf Pro and JSC service configuration |
| Endpoint Security | `endpoint-security-*` | CrowdStrike, FileVault, Microsoft Defender |
| Management | `management-*` | macOS/iOS device management, app installers |
| Network Security | `network-security-*` | Content filtering, threat defense, ZTNA |

### Module Internal Structure
```
module-name/
├── main.tf                    # Resource definitions (required)
├── variables.tf               # Input variables (required)
├── README.md                  # Documentation (required)
└── support_files/             # Resource files (optional)
    ├── computer_scripts/      # Shell scripts (.sh)
    ├── computer_config_profiles/    # macOS configs (.mobileconfig)
    ├── computer_extension_attributes/
    └── mobile_configuration_profiles/  # iOS/iPadOS configs
```

### Provider Aliasing Pattern

Root providers use aliases (`jpro`, `jsc`). Modules declare `configuration_aliases` and receive providers via `providers` block:

```hcl
# In module main.tf
terraform {
  required_providers {
    jamfpro = {
      source                = "deploymenttheory/jamfpro"
      configuration_aliases = [jamfpro.jpro]
    }
  }
}

# In root main.tf calling the module
module "example" {
  source = "./modules/example"
  providers = {
    jamfpro.jpro = jamfpro.jpro
  }
}
```

### Feature Flags

Modules are conditionally enabled via boolean variables in `terraform.tfvars`. The `spec.yml` file defines all available options and their corresponding modules.

```hcl
# Example: conditional module inclusion
module "compliance-macOS-cis-level-1" {
  count  = var.include_mac_cis_lvl1_benchmark == true ? 1 : 0
  source = "./modules/compliance-macOS-cis-level-1"
  # ...
}
```

## Key Files

| File | Purpose |
|------|---------|
| `main.tf` | Root module orchestration - all module calls |
| `variables.tf` | Root input variables (credentials, feature flags) |
| `providers.tf` | Provider configuration with aliases |
| `spec.yml` | Module specification - defines all options and credentials |

## API Configuration

The Jamf Pro API requires specific settings to avoid rate limiting:

```hcl
provider "jamfpro" {
  mandatory_request_delay_milliseconds = 100
  jamfpro_load_balancer_lock           = true
  token_refresh_buffer_period_seconds  = 5
  hide_sensitive_data                  = true
}
```

Always run `export TF_CLI_ARGS_apply="-parallelism=1"` before applying.

## Git Workflow

- **main** - Production (protected; PRs only from `staging` or `hotfix/*`)
- **staging** - Pre-production testing
- Feature branches PR to staging first

## CI Checks

PRs must pass:
1. `terraform init`
2. `terraform fmt -check -recursive`

## Testing & PR Requirements

See [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Testing workflow and commands
- PR checklist and code review standards
- Branch strategy

See [testing/README.md](./testing/README.md) for:
- Setting up test credentials
- Running `terraform plan` and `terraform apply`

## Security

**Critical requirements:**
- Never hardcode credentials in `.tf` files
- All `*_secret`, `*_password` variables must have `sensitive = true`
- Never commit `.tfstate` files (contains secrets in plaintext)

See [STYLE_GUIDE.md](./STYLE_GUIDE.md#security-checklist) for full security checklist.

## Documentation

- [Terraform Docs](https://developer.hashicorp.com/terraform/docs)
- [jamfpro Provider](https://registry.terraform.io/providers/deploymenttheory/jamfpro/latest/docs)
- [jsc Provider](https://registry.terraform.io/providers/Jamf-Concepts/jsctfprovider/latest/docs)
