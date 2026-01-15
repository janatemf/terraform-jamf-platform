# Testing Guide

How to test modules in terraform-jamf-platform.

## Quick Start

```bash
# 1. Create test variables file
cp testing/test.tfvars.example testing/test.tfvars

# 2. Edit with your test configuration
nano testing/test.tfvars

# 3. Run validation
terraform fmt -check -recursive
terraform validate

# 4. Plan with test variables
terraform plan -var-file=testing/test.tfvars

# 5. Apply (to test environment only)
export TF_CLI_ARGS_apply="-parallelism=1"
terraform apply -var-file=testing/test.tfvars
```

## Setting Up test.tfvars

Create `testing/test.tfvars` with:

### Required Credentials

```hcl
# Jamf Pro credentials (required for most modules)
jamfpro_auth_method   = "oauth2"
jamfpro_instance_url  = "https://your-instance.jamfcloud.com"
jamfpro_client_id     = "your-client-id"
jamfpro_client_secret = "your-client-secret"

# Jamf Security Cloud (required for JSC modules)
jsc_username           = "your-username"
jsc_password           = "your-password"
jsc_application_id     = "your-app-id"
jsc_application_secret = "your-app-secret"

# Jamf Protect (required for Protect modules)
jamfprotect_url             = "https://your-org.protect.jamfcloud.com"
jamfprotect_client_id       = "your-protect-client-id"
jamfprotect_client_password = "your-protect-client-password"
```

### Module Feature Flags

Enable only the modules you want to test:

```hcl
# Example: Test compliance module
include_mac_cis_lvl1_benchmark = true

# Example: Test app installer
include_google_chrome = true

# Example: Test JSC integration
include_jsc_uemc = true
```

## Validation Commands

### Before Every Commit

```bash
# Check formatting
terraform fmt -check -recursive

# Fix formatting issues
terraform fmt -recursive

# Validate syntax
terraform validate
```

### Before Every PR

```bash
# Preview all changes
terraform plan -var-file=testing/test.tfvars

# Check for unexpected changes
terraform plan -var-file=testing/test.tfvars | grep -E "^(  #|Plan:)"
```

## Testing Specific Modules

### Testing a Single Module

1. Set only that module's flag to `true` in test.tfvars
2. Set all other flags to `false`
3. Run `terraform plan` to verify

```hcl
# test.tfvars - testing only CIS benchmark
include_mac_cis_lvl1_benchmark = true
include_mac_stig_benchmark     = false
include_filevault              = false
# ... all others false
```

### Testing Module Combinations

Some modules have dependencies. Test combinations:

```hcl
# JSC + Jamf Pro integration
include_jsc_uemc         = true
include_jsc_all_services = true
```

## Expected Outputs

### Successful Plan

```
Plan: X to add, 0 to change, 0 to destroy.
```

### Successful Apply

```
Apply complete! Resources: X added, 0 changed, 0 destroyed.
```

### Common Errors

**API Rate Limiting:**
```
Error: API Error
```
Fix: Ensure `parallelism=1` is set

**Authentication Failed:**
```
Error: authentication failed
```
Fix: Verify credentials in test.tfvars

**Resource Already Exists:**
```
Error: resource already exists
```
Fix: Import existing resource or use different name

## Cleanup

After testing, destroy resources:

```bash
terraform destroy -var-file=testing/test.tfvars
```

## Important Notes

- **Never use production credentials** for testing
- **test.tfvars is gitignored** - it will not be committed
- **Test in isolated environment** when possible
- **Review plan output carefully** before applying

## File Handling

The `test.tfvars` file:
- Is excluded from git via `.gitignore`
- Should contain only test-specific overrides
- Will be cleaned up by future CI automation

Create `test.tfvars.example` (without secrets) if you want to share test configurations.
