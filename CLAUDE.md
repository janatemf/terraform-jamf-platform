# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Terraform project for configuring Jamf platform components including Jamf Pro, Jamf Security Cloud (JSC), and Jamf Protect. It provides modular configurations for compliance benchmarks, device management, endpoint security, and network security across macOS and iOS devices.

## Architecture

### Module-Based Structure
- **Root Configuration**: `/main.tf` defines provider configurations and calls all modules
- **Modular Design**: Each module in `/modules/` represents a specific configuration set
- **Provider Aliases**: Uses aliased providers (`jamfpro.jpro`, `jsc.jsc`) for module isolation

### Module Categories
- **Compliance**: CIS, DISA STIG, NIST 800-171, CMMC benchmarks for macOS and iOS
- **Configuration**: Jamf Pro admin settings, categories, smart groups, activation codes
- **Endpoint Security**: FileVault, Microsoft Defender, CrowdStrike, Jamf Protect
- **Management**: App installers, device configuration profiles, SSO integration
- **Network Security**: Content filtering, zero trust network access, threat defense
- **Onboarder**: Grouped configurations for quick deployment scenarios

### Provider Configuration
- **Jamf Pro Provider**: Uses deploymenttheory/jamfpro v0.21.0 with mandatory 100ms request delays
- **JSC Provider**: Uses danjamf/jsctfprovider >=0.0.23 for Jamf Security Cloud
- **AWS Provider**: Optional for SaaS tenancy control (commented out in variables.tf)

## Development Commands

### Essential Terraform Commands
```bash
# Initialize providers (run before first apply)
terraform init -upgrade

# Format code (required before applying)
terraform fmt

# Plan changes
terraform plan

# Apply with reduced parallelism (recommended)
export TF_CLI_ARGS_apply="-parallelism=1"
terraform apply

# Destroy resources
terraform destroy
```

### Required Environment Setup
Create `terraform.tfvars` with required credentials:
- Jamf Pro: instance URL, client ID/secret or username/password
- Jamf Security Cloud: username, password, application ID/secret  
- Jamf Protect: URL, client ID/password (optional)

## Key Configuration Patterns

### Module Enablement
Modules are conditionally enabled via boolean variables (e.g., `include_mac_cis_lvl1_benchmark = true`)

### Provider Passing
Each module call includes a `providers` block mapping aliases to root providers

### Variable Organization
- Main variables in `variables.tf`
- Onboarder-specific variables in `variables_onboarder_wizard.tf`
- All sensitive variables marked appropriately

### Support Files
Modules contain `support_files/` directories with:
- `.mobileconfig` profiles for device configuration
- Shell scripts for compliance checking and installation
- Extension attributes for reporting

## Testing
- Use `/testing/` directory with `test.tfvars` for module testing
- Test variables are cleaned up during PR process to staging branch

## Demo Server Setup
This repository includes automated daily reset functionality for demo environments:

### Daily Reset Workflow
- **Location**: `.github/workflows/daily-demo-reset.yml`
- **Schedule**: Daily at 6 AM UTC (configurable)
- **Purpose**: Clean slate for sales demonstrations

### Components
- **Cleanup Script**: `scripts/jamf-cleanup-headless.sh` - Removes all Jamf Pro objects
- **Demo Config**: Pre-configured onboarder modules for comprehensive demos
- **Verification**: Automated checks to ensure successful deployment

### Required GitHub Secrets
- `JAMF_URL`, `JAMF_USERNAME`, `JAMF_PASSWORD` - Jamf Pro credentials
- `JAMF_CLIENT_ID`, `JAMF_CLIENT_SECRET` - OAuth2 credentials (if used)
- JSC and Jamf Protect credentials (optional)

### Usage
1. Configure GitHub secrets with Jamf Pro credentials
2. Create `demo` environment in repository settings
3. Workflow runs automatically or trigger manually
4. Demo server resets to clean state with sample configurations

See `DEMO-SETUP.md` for detailed setup instructions.

## API Considerations
- Jamf Pro provider configured with 100ms mandatory request delays
- Parallelism should be limited to 1 to avoid API errors
- Load balancer lock enabled for Jamf Pro provider