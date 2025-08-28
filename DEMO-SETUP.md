# Demo Server Daily Reset Setup

This setup provides an automated daily reset of your Jamf Pro demo server using GitHub Actions. Perfect for sales teams who need a clean demo environment every day.

## Overview

The system works by:
1. **Daily Cleanup**: Runs a script to delete all Jamf Pro objects
2. **Fresh Deployment**: Applies Terraform configuration with onboarder modules
3. **Verification**: Confirms the demo environment is ready

## Setup Instructions

### 1. GitHub Repository Configuration

#### Required GitHub Secrets
Navigate to your repository settings → Secrets and Variables → Actions, and add these secrets:

**Jamf Pro Credentials:**
- `JAMF_URL`: Your Jamf Pro server URL (e.g., `https://yourserver.jamfcloud.com`)
- `JAMF_USERNAME`: Jamf Pro admin username
- `JAMF_PASSWORD`: Jamf Pro admin password
- `JAMF_CLIENT_ID`: OAuth2 client ID (if using OAuth2)
- `JAMF_CLIENT_SECRET`: OAuth2 client secret (if using OAuth2)

**Jamf Security Cloud Credentials (optional):**
- `JSC_USERNAME`: JSC username
- `JSC_PASSWORD`: JSC password  
- `JSC_APPLICATION_ID`: JSC application ID
- `JSC_APPLICATION_SECRET`: JSC application secret

**Jamf Protect Credentials (optional):**
- `JAMF_PROTECT_URL`: Jamf Protect instance URL
- `JAMF_PROTECT_CLIENT_ID`: Protect client ID
- `JAMF_PROTECT_CLIENT_PASSWORD`: Protect client password

#### GitHub Environment
1. Create a new environment called `demo` in repository settings
2. Add environment protection rules if needed
3. The workflow is configured to use this environment

### 2. Workflow Configuration

The workflow file `.github/workflows/daily-demo-reset.yml` includes:

- **Schedule**: Runs daily at 6 AM UTC (modify the cron schedule as needed)
- **Manual Trigger**: Can be triggered manually via GitHub Actions UI
- **Parallelism**: Limited to 1 to avoid Jamf Pro API rate limits
- **Error Handling**: Cleanup on failure and detailed logging

### 3. Customizing Demo Configuration

The workflow is pre-configured with sensible demo defaults, but you can customize:

1. **Edit the workflow file** to modify which modules are enabled
2. **Copy `demo.tfvars.example`** to create custom configurations
3. **Modify the Terraform variables** in the workflow's `env` section

**Current Demo Configuration:**
- ✅ Onboarder modules (all)
- ✅ macOS and iOS CIS Level 1 compliance
- ✅ Categories and Smart Groups
- ✅ Microsoft 365, FileVault, Rosetta
- ✅ Common app installers (Chrome, Firefox, Slack, Zoom, Edge)
- ❌ Advanced security modules (by default)
- ❌ JSC modules (requires separate credentials)

### 4. Testing the Setup

#### Manual Test Run
1. Go to GitHub Actions in your repository
2. Select "Daily Demo Server Reset" workflow
3. Click "Run workflow" to test manually
4. Monitor the execution logs

#### Verify Results
After a successful run:
1. Log into your Jamf Pro server
2. Check that demo objects have been created:
   - Categories
   - Configuration Profiles  
   - Policies
   - Smart Computer Groups
   - App installers

## Workflow Details

### Cleanup Process
The `scripts/jamf-cleanup-headless.sh` script:
- Authenticates to Jamf Pro using basic auth
- Deletes all JSS Resource objects (policies, profiles, etc.)
- Deletes app installer deployments via API
- Logs all actions to `/tmp/jamf_pro_cleanup_headless.log`
- Runs completely headless (no user interaction)

### Demo Deployment
The Terraform apply process:
- Uses parallelism=1 to respect API limits
- Enables comprehensive demo modules
- Includes error handling and verification
- Provides detailed logging of created objects

### Schedule
- **Default**: Daily at 6 AM UTC
- **Timezone**: Modify the cron expression in the workflow file
- **Frequency**: Can be changed to hourly, weekly, etc.

Example cron schedules:
```yaml
- cron: "0 */6 * * *"    # Every 6 hours
- cron: "0 9 * * 1-5"    # Weekdays at 9 AM
- cron: "0 6 * * *"      # Daily at 6 AM (current)
```

## Troubleshooting

### Common Issues

**Authentication Failures:**
- Verify GitHub secrets are correctly set
- Check Jamf Pro credentials have sufficient privileges
- Ensure API access is enabled in Jamf Pro

**Terraform Errors:**
- Review the workflow logs for specific error messages  
- Check if Jamf Pro provider version is compatible
- Verify terraform state isn't corrupted

**Cleanup Script Issues:**
- Ensure the script has necessary permissions
- Check if plutil/xmllint dependencies are available
- Verify Jamf Pro health check endpoint is accessible

### Monitoring and Alerts

The workflow includes:
- ✅ Success/failure notifications in the workflow summary
- 📊 Object count verification after deployment
- 🔍 Detailed logging for troubleshooting
- 🧹 Automatic cleanup on failure

### Manual Intervention

If you need to manually reset:
1. Run the cleanup script directly on the Jamf Pro server
2. Use Terraform destroy followed by apply
3. Check the workflow logs for specific failed modules

## Security Considerations

- All credentials stored as GitHub secrets (encrypted)
- Scripts run in isolated GitHub Actions environment
- No persistent state stored between runs
- Cleanup script uses secure authentication methods

## Support

For issues with this setup:
1. Check GitHub Actions workflow logs
2. Review Jamf Pro system logs
3. Validate Terraform provider compatibility
4. Ensure all required GitHub secrets are configured