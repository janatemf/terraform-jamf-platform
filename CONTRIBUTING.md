# Contributing to terraform-jamf-platform

Guidelines for contributing to this Terraform project for Jamf automation.

## Prerequisites

### Required Tools

- **Terraform** >= 1.0 ([Install Guide](https://developer.hashicorp.com/terraform/install))
- **Git** for version control

### Required Access

- Jamf Pro instance with API credentials (Client ID + Secret)
- Jamf Security Cloud credentials (if working on JSC modules)
- Jamf Protect credentials (if working on Protect modules)

### Local Setup

1. Clone the repository
2. Copy credential template:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
3. Edit `terraform.tfvars` with your credentials
4. Initialize Terraform:
   ```bash
   terraform init -upgrade
   ```

## Development Workflow

### Branch Strategy

```
main (production)
  ↑
staging (pre-production testing)
  ↑
feature/your-feature (your work)
```

1. **Create feature branch** from `staging`:
   ```bash
   git checkout staging
   git pull origin staging
   git checkout -b feature/your-feature
   ```

2. **Make changes** following the [Style Guide](./STYLE_GUIDE.md)

3. **Test locally** (see Testing section below)

4. **Push and create PR** to `staging`:
   ```bash
   git push -u origin feature/your-feature
   ```

5. **After staging approval**, changes merge to `main`

### Hotfixes

For urgent production fixes, use `hotfix/*` branches which can PR directly to `main`:
```bash
git checkout main
git checkout -b hotfix/critical-fix
```

## Creating New Modules

### 1. Choose the Right Category

| Category | Purpose |
|----------|---------|
| `compliance-` | Security benchmarks (CIS, STIG, NIST) |
| `configuration-` | Jamf Pro/JSC service configuration |
| `endpoint-security-` | Endpoint protection (FileVault, Defender) |
| `management-` | Device management, app installers |
| `network-security-` | Network policies, content filtering |
| `onboarder-` | Bundled parent modules |

### 2. Name Your Module

Pattern: `<category>-<platform>-<feature>`

Examples:
- `compliance-macOS-cis-level-2`
- `management-iOS-app-restrictions`
- `endpoint-security-macOS-sentinelone`

### 3. Create Required Files

```bash
mkdir -p modules/your-module-name
```

See [MODULE_TEMPLATE.md](./MODULE_TEMPLATE.md) for starter templates.

**Required files:**
- `main.tf` - Resource definitions
- `variables.tf` - Input variables
- `README.md` - Module documentation

**Optional:**
- `outputs.tf` - If module exposes values
- `locals.tf` - If module has 3+ local values
- `support_files/` - Scripts, profiles, extension attributes

### 4. Update spec.yml

Add your module option:

```yaml
options:
  - key: include_your_feature
    type: <boolean>
    presence: optional
    module_name: module.your-module-name
    required_provider: jpro
    category: Category Name
    display_name: Feature Display Name
    display_desc: Description of what this module does
```

### 5. Add Module Call to main.tf

```hcl
module "your-module-name" {
  count  = var.include_your_feature ? 1 : 0
  source = "./modules/your-module-name"

  jamfpro_instance_url  = var.jamfpro_instance_url
  jamfpro_client_id     = var.jamfpro_client_id
  jamfpro_client_secret = var.jamfpro_client_secret

  providers = {
    jamfpro.jpro = jamfpro.jpro
  }
}
```

### 6. Add Example

Create `examples/your-module-name/main.tf` with usage example.

## Updating Existing Modules

### Before Making Changes

1. Read the existing module code thoroughly
2. Understand the resource dependencies
3. Check if changes affect other modules
4. Review the module's README.md

### Guidelines

- **Preserve backwards compatibility** when possible
- **Update README.md** with any new variables or behaviors
- **Update spec.yml** if adding new options
- **Test with existing configurations** before submitting

### Adding Resources to Existing Modules

Follow the established resource creation order:
1. Categories
2. Scripts
3. Extension Attributes
4. Smart Groups
5. Policies
6. Configuration Profiles

## Testing Requirements

### Before Every Commit

```bash
# Format check (must pass CI)
terraform fmt -check -recursive

# Auto-format if needed
terraform fmt -recursive

# Validate configuration
terraform validate
```

### Before Every PR

```bash
# Set parallelism for API stability
export TF_CLI_ARGS_apply="-parallelism=1"

# Plan your changes
terraform plan

# Apply to test environment (if you have one)
terraform apply
```

### Testing Checklist

- [ ] `terraform fmt -check -recursive` passes
- [ ] `terraform validate` passes
- [ ] `terraform plan` shows expected changes
- [ ] No sensitive values in output
- [ ] Module works with `count = 0` (disabled state)
- [ ] Module works with `count = 1` (enabled state)

## PR Checklist

Before submitting your PR, verify:

### Code Quality
- [ ] Follows naming conventions in [STYLE_GUIDE.md](./STYLE_GUIDE.md)
- [ ] All variables have descriptions
- [ ] Sensitive variables marked with `sensitive = true`
- [ ] No hardcoded credentials or secrets
- [ ] `terraform fmt -recursive` applied

### Documentation
- [ ] Module has README.md
- [ ] Example added to `/examples/` directory
- [ ] `spec.yml` updated (if adding new options)
- [ ] Complex logic has comments

### Testing
- [ ] `terraform validate` passes
- [ ] `terraform plan` reviewed
- [ ] `terraform apply` tested locally (if possible)

### PR Description
- [ ] Summary of changes included
- [ ] Type of change identified (bug fix, feature, etc.)
- [ ] Breaking changes noted (if any)

## Code Review Standards

### What Reviewers Look For

1. **Security**
   - No hardcoded secrets
   - Sensitive variables properly marked
   - Appropriate scoping (not overly permissive)

2. **Correctness**
   - Resources created in proper order
   - Dependencies correctly expressed
   - Variable types match usage

3. **Style**
   - Follows naming conventions
   - Consistent formatting
   - Clear resource identifiers

4. **Documentation**
   - README explains module purpose
   - Variables have descriptions
   - Non-obvious logic has comments

### Responding to Review Feedback

- Address all comments before requesting re-review
- Explain reasoning if you disagree with feedback
- Mark conversations as resolved when addressed

## Getting Help

- **Style questions**: See [STYLE_GUIDE.md](./STYLE_GUIDE.md)
- **Module templates**: See [MODULE_TEMPLATE.md](./MODULE_TEMPLATE.md)
- **AI assistance**: See [AGENTS.md](./AGENTS.md) or [CLAUDE.md](./CLAUDE.md)
- **Terraform docs**: [developer.hashicorp.com/terraform](https://developer.hashicorp.com/terraform/docs)
- **Provider docs**:
  - [jamfpro](https://registry.terraform.io/providers/deploymenttheory/jamfpro/latest/docs)
  - [jsc](https://registry.terraform.io/providers/Jamf-Concepts/jsctfprovider/latest/docs)
