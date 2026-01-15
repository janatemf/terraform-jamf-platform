# Jamf Security Cloud - Delete All Resources

This directory contains tools to delete all resources from a Jamf Security Cloud tenant. This is useful for testing, cleanup, or decommissioning tenants.

## Contents

- `delete_all_jsc_resources.py` - Python script that deletes all resources
- `.github/workflows/delete-jsc-tenant.yml` - GitHub Actions workflow for automated deletion

## What Gets Deleted

The script will delete ALL of the following resource types from your JSC tenant:

### Jamf Security Cloud (Radar) Resources:
1. **ZTNA Policies** - Zero Trust Network Access application definitions
2. **Activation Profiles** - Device enrollment profiles
3. **Hostname Mappings** - Custom DNS mappings
4. **Block Pages** - Custom block page configurations (reset to defaults)
5. **UEM Connectors** - Jamf Pro integration configurations
6. **Okta IdP Connections** - Identity provider integrations

### Private Access Gateway (PAG) Resources (optional):
7. **PAG ZTNA Applications** - Private access applications

### Jamf Protect Resources (optional):
8. **Prevent Lists** - Hash/signing ID/team ID prevention lists

## Prerequisites

### For Local Script Execution:
- Python 3.7 or higher
- `requests` library: `pip install requests`
- JSC credentials (username/password)
- Optional: PAG credentials (application ID/secret)
- Optional: Protect credentials (client ID/password)

### For GitHub Actions:
- GitHub repository with Actions enabled
- Repository secrets configured (see Configuration section below)

## Usage

### Option 1: Local Execution

#### Basic usage (Radar resources only):
```bash
python delete_all_jsc_resources.py \
  --username "your-jsc-username" \
  --password "your-jsc-password"
```

#### With customer ID specified:
```bash
python delete_all_jsc_resources.py \
  --username "your-jsc-username" \
  --password "your-jsc-password" \
  --customer-id "12345"
```

#### Include PAG resources:
```bash
python delete_all_jsc_resources.py \
  --username "your-jsc-username" \
  --password "your-jsc-password" \
  --pag-app-id "your-pag-app-id" \
  --pag-app-secret "your-pag-secret"
```

#### Include Jamf Protect resources:
```bash
python delete_all_jsc_resources.py \
  --username "your-jsc-username" \
  --password "your-jsc-password" \
  --protect-domain "yourcompany.protect.jamfcloud.com" \
  --protect-client-id "your-protect-client-id" \
  --protect-client-password "your-protect-password"
```

#### Dry run (see what would be deleted without actually deleting):
```bash
python delete_all_jsc_resources.py \
  --username "your-jsc-username" \
  --password "your-jsc-password" \
  --dry-run
```

#### Non-interactive mode (for automation):
```bash
python delete_all_jsc_resources.py \
  --username "your-jsc-username" \
  --password "your-jsc-password" \
  --non-interactive
```

### Option 2: GitHub Actions Workflow

The workflow is configured to run manually via `workflow_dispatch`.

#### Setup:

1. **Configure Repository Secrets** (Settings → Secrets and variables → Actions):

   **Required secrets:**
   - `JSC_USERNAME` - Your JSC username
   - `JSC_PASSWORD` - Your JSC password

   **Optional secrets:**
   - `JSC_DOMAIN` - JSC domain (defaults to `radar.wandera.com`)
   - `JSC_CUSTOMER_ID` - Customer ID (auto-discovered if not provided)
   - `JSC_PAG_APP_ID` - PAG application ID
   - `JSC_PAG_APP_SECRET` - PAG application secret
   - `JSC_PROTECT_DOMAIN` - Protect domain (e.g., `company.protect.jamfcloud.com`)
   - `JSC_PROTECT_CLIENT_ID` - Protect client ID
   - `JSC_PROTECT_CLIENT_PASSWORD` - Protect client password

2. **Run the Workflow**:
   - Go to "Actions" tab in your GitHub repository
   - Select "Delete JSC Tenant Resources" workflow
   - Click "Run workflow"
   - **Type `DELETE ALL` in the confirmation field**
   - Check the boxes for PAG/Protect if you want to delete those resources
   - Click "Run workflow" button

#### Safety Features:

The GitHub workflow includes multiple safety checks:
1. **Manual trigger only** - Cannot be triggered automatically
2. **Confirmation required** - You must type `DELETE ALL` exactly
3. **Explicit opt-in for PAG/Protect** - Must check boxes to delete these resources
4. **Detailed logging** - All deletions are logged in the workflow run

## Script Parameters

```
Required:
  --username              JSC username
  --password              JSC password

Optional:
  --domain               JSC domain (default: radar.wandera.com)
  --customer-id          Customer ID (auto-discovered if not provided)
  --pag-app-id           PAG application ID
  --pag-app-secret       PAG application secret
  --protect-domain       Jamf Protect domain
  --protect-client-id    Jamf Protect client ID
  --protect-client-password  Jamf Protect client password
  --dry-run              Show what would be deleted without deleting
  --non-interactive      Skip confirmation prompt (for CI/CD)
```

## Deletion Order

Resources are deleted in dependency order to avoid conflicts:

1. ZTNA policies and PAG ZTNA applications (dependent on routes)
2. Activation profiles
3. Hostname mappings
4. Block pages (reset to defaults)
5. UEM connectors
6. Okta IdP connections
7. Jamf Protect prevent lists

## Authentication

The script supports three authentication systems:

### 1. Radar API (Required)
- Username/password authentication
- Session cookie-based with XSRF tokens
- Auto-discovers customer ID if not provided
- Supports both parent and customer account types

### 2. PAG API (Optional)
- Application ID and secret
- JWT bearer token authentication
- Only used if credentials are provided

### 3. Jamf Protect API (Optional)
- Client ID and password
- Token-based authentication
- Only used if credentials are provided

## Safety Warnings

⚠️ **WARNING: THIS OPERATION IS DESTRUCTIVE AND IRREVERSIBLE**

- All resources will be **permanently deleted**
- There is **no undo** or recovery mechanism
- The script requires explicit confirmation before executing
- Use `--dry-run` first to see what will be deleted
- Test in a non-production environment first

## Output Example

```
======================================================================
JAMF SECURITY CLOUD - DELETE ALL RESOURCES
======================================================================

*** WARNING: This will delete ALL resources from your tenant ***
*** This operation CANNOT be undone ***

Type 'DELETE ALL' to confirm: DELETE ALL

[START] Beginning deletion process...

[DELETE] Fetching ZTNA policies...
[DELETE] Deleting ZTNA policy: Sales VPN (ID: 123)
[SUCCESS] Deleted ZTNA policy: Sales VPN

[DELETE] Fetching activation profiles...
[DELETE] Deleting activation profile: iOS BYOD (ID: 456)
[SUCCESS] Deleted activation profile: iOS BYOD

...

======================================================================
DELETION SUMMARY
======================================================================
Successfully deleted: 15 resource(s)
Failed to delete: 0 resource(s)
======================================================================
```

## Error Handling

- Each deletion is attempted independently
- Failed deletions are logged but don't stop the process
- Final summary shows successful vs failed deletions
- Non-zero exit code if authentication fails
- Detailed error messages for troubleshooting

## Rate Limiting

The script includes a 0.5 second delay between deletions to avoid overwhelming the API.

## Troubleshooting

### Authentication Failures

**Problem**: `[ERROR] Failed to obtain XSRF token`
- Check username and password are correct
- Verify the domain is correct (default: radar.wandera.com)
- Ensure account is not using SSO (script only supports local auth)

**Problem**: `[ERROR] Unknown account type`
- Contact JSC support to verify your account configuration

### Deletion Failures

**Problem**: Some resources fail to delete
- Check if resources are in use or have dependencies
- Run the script again - it will skip already-deleted resources
- Review error messages for specific API errors

### PAG/Protect Issues

**Problem**: PAG/Protect resources not deleted
- Verify credentials are correct
- Ensure you have appropriate permissions
- Check the domain format for Protect

## Contributing

If you find issues or want to add features:
1. The script is self-contained in `delete_all_jsc_resources.py`
2. The GitHub workflow is in `.github/workflows/delete-jsc-tenant.yml`
3. Update this README if you add new resource types

## License

This script is provided as-is for use with the terraform-provider-jsctfprovider project.

## Related Files

- `main.go` - Terraform provider main entry point (see for resource definitions)
- `internal/auth/auth.go` - Authentication implementation reference
- `endpoints/*/resource_*.go` - Individual resource implementations
