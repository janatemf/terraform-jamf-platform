#!/usr/bin/env python3
"""
Jamf Security Cloud - Delete All Resources Script

This script deletes ALL resources from a Jamf Security Cloud tenant.
USE WITH EXTREME CAUTION - THIS OPERATION CANNOT BE UNDONE.

Authentication requirements:
1. Radar API: JSC username/password and customer ID
2. PAG API: Application ID and secret (optional, if you have PAG resources)
3. Protect API: Client ID and password (optional, if you have Protect resources)
"""

import requests
import json
import sys
import argparse
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import time


@dataclass
class JSCConfig:
    """Configuration for JSC API connections"""
    domain: str
    username: str
    password: str
    customer_id: Optional[str] = None

    # PAG (Private Access Gateway) credentials
    application_id: Optional[str] = None
    application_secret: Optional[str] = None

    # Jamf Protect credentials
    protect_domain: Optional[str] = None
    protect_client_id: Optional[str] = None
    protect_client_password: Optional[str] = None


class JSCAuthenticator:
    """Handles authentication to JSC APIs"""

    def __init__(self, config: JSCConfig):
        self.config = config
        self.session = requests.Session()
        self.xsrf_token: Optional[str] = None
        self.pag_token: Optional[str] = None
        self.protect_token: Optional[str] = None

    def authenticate_radar(self) -> bool:
        """Authenticate to Radar API and discover customer ID if needed"""
        print("[AUTH] Authenticating to Radar API...")

        try:
            # Step 1: Get cookies by calling login-methods endpoint
            login_methods_url = f"https://{self.config.domain}/auth/v1/login-methods?email={self.config.username}"
            print(f"[AUTH] Getting cookies from login-methods endpoint...")

            response = self.session.get(login_methods_url)
            response.raise_for_status()

            # Extract XSRF token from cookies
            self.xsrf_token = self.session.cookies.get('XSRF-TOKEN')

            if not self.xsrf_token:
                print("[ERROR] Failed to obtain XSRF token from cookies")
                return False

            print(f"[AUTH] Obtained XSRF token from cookies")

            # Step 2: Authenticate with credentials
            auth_url = f"https://{self.config.domain}/auth/v1/credentials"
            payload = {
                "username": self.config.username,
                "password": self.config.password,
                "totp": "",
                "backupCode": ""
            }

            auth_response = self.session.post(
                auth_url,
                json=payload,
                headers={'X-Xsrf-Token': self.xsrf_token}
            )
            auth_response.raise_for_status()

            # Verify we have SESSION cookie
            session_cookie = self.session.cookies.get('SESSION')
            if not session_cookie:
                print("[ERROR] Failed to obtain SESSION cookie")
                return False

            print("[AUTH] Successfully authenticated and obtained SESSION cookie")

            # Discover customer ID if not provided
            if not self.config.customer_id:
                self._discover_customer_id()

            print("[AUTH] Radar API authentication successful")
            return True

        except Exception as e:
            print(f"[ERROR] Radar authentication failed: {e}")
            return False

    def _discover_customer_id(self):
        """Discover customer ID from /auth/v1/me endpoint"""
        try:
            me_url = f"https://{self.config.domain}/auth/v1/me"
            response = self.session.get(
                me_url,
                headers={'X-Xsrf-Token': self.xsrf_token}
            )
            response.raise_for_status()

            data = response.json()

            # Check if user is customer or parent type
            entity_type = data.get('admin', {}).get('entityType')

            if entity_type == 'CUSTOMER':
                self.config.customer_id = str(data.get('admin', {}).get('entityId'))
                print(f"[AUTH] Discovered customer ID (CUSTOMER type): {self.config.customer_id}")
            elif entity_type == 'PARENT':
                # Get first visible customer for parent accounts
                customers_url = f"https://{self.config.domain}/gate/user-service/customer/v2/customers/visible-for-admin"
                cust_response = self.session.get(
                    customers_url,
                    headers={'X-Xsrf-Token': self.xsrf_token}
                )
                cust_response.raise_for_status()
                customers = cust_response.json()

                # Find first leaf customer
                for customer in customers:
                    if customer.get('leaf'):
                        self.config.customer_id = str(customer.get('customerId'))
                        print(f"[AUTH] Discovered customer ID (PARENT type): {self.config.customer_id}")
                        break
            else:
                print(f"[ERROR] Unknown entity type: {entity_type}")

        except Exception as e:
            print(f"[ERROR] Failed to discover customer ID: {e}")

    def authenticate_pag(self) -> bool:
        """Authenticate to PAG API"""
        if not self.config.application_id or not self.config.application_secret:
            print("[SKIP] PAG credentials not provided, skipping PAG authentication")
            return False

        print("[AUTH] Authenticating to PAG API...")

        pag_auth_url = "https://api.wandera.com/v1/login"

        try:
            response = requests.post(
                pag_auth_url,
                auth=(self.config.application_id, self.config.application_secret)
            )
            response.raise_for_status()

            auth_data = response.json()
            self.pag_token = auth_data.get('token')

            if not self.pag_token:
                print("[ERROR] Failed to obtain PAG token")
                return False

            print("[AUTH] PAG API authentication successful")
            return True

        except Exception as e:
            print(f"[ERROR] PAG authentication failed: {e}")
            return False

    def authenticate_protect(self) -> bool:
        """Authenticate to Jamf Protect API"""
        if not self.config.protect_domain or not self.config.protect_client_id or not self.config.protect_client_password:
            print("[SKIP] Protect credentials not provided, skipping Protect authentication")
            return False

        print("[AUTH] Authenticating to Jamf Protect API...")

        protect_token_url = f"https://{self.config.protect_domain}/token"
        payload = {
            "client_id": self.config.protect_client_id,
            "password": self.config.protect_client_password
        }

        try:
            response = requests.post(protect_token_url, json=payload)
            response.raise_for_status()

            token_data = response.json()
            self.protect_token = token_data.get('token')

            if not self.protect_token:
                print("[ERROR] Failed to obtain Protect token")
                return False

            print("[AUTH] Jamf Protect API authentication successful")
            return True

        except Exception as e:
            print(f"[ERROR] Protect authentication failed: {e}")
            return False


class JSCResourceDeleter:
    """Deletes resources from JSC tenant"""

    def __init__(self, config: JSCConfig, auth: JSCAuthenticator):
        self.config = config
        self.auth = auth
        self.deleted_count = 0
        self.failed_count = 0

    def _radar_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make authenticated request to Radar API"""
        url = f"https://{self.config.domain}{endpoint}"

        # Replace {customerid} placeholder in path
        url = url.replace('{customerid}', self.config.customer_id)

        # Add customerId as query parameter (required by all Radar API endpoints)
        params = kwargs.pop('params', {})
        params['customerId'] = self.config.customer_id

        headers = kwargs.pop('headers', {})
        headers['X-Xsrf-Token'] = self.auth.xsrf_token
        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'

        try:
            response = self.auth.session.request(method, url, headers=headers, params=params, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            # 404 usually means the resource doesn't exist, which is ok for GET requests
            if e.response.status_code == 404 and method == 'GET':
                print(f"[INFO] Resource not found (404): {endpoint}")
                return None
            print(f"[ERROR] Request failed: {method} {url} - {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Request failed: {method} {url} - {e}")
            return None

    def _pag_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Make authenticated request to PAG API"""
        url = f"https://api.wandera.com{endpoint}"

        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self.auth.pag_token}'

        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"[ERROR] Request failed: {method} {url} - {e}")
            return None

    def _protect_request(self, query: str, variables: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated GraphQL request to Protect API"""
        url = f"https://{self.config.protect_domain}/graphql"

        headers = {
            'Authorization': f'Bearer {self.auth.protect_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'query': query,
            'variables': variables or {}
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ERROR] GraphQL request failed: {e}")
            return None

    def delete_okta_idps(self) -> int:
        """Delete all Okta IdP connections"""
        print("\n[DELETE] Fetching Okta IdP connections...")

        response = self._radar_request('GET', '/gate/identity-service/v1/connections')
        if not response:
            return 0

        connections = response.json()
        if not connections:
            print("[INFO] No Okta IdP connections found")
            return 0

        count = 0
        for conn in connections:
            conn_id = conn.get('id')
            conn_name = conn.get('name', 'Unknown')
            print(f"[DELETE] Deleting Okta IdP: {conn_name} (ID: {conn_id})")

            delete_response = self._radar_request('DELETE', f'/gate/identity-service/v1/connections/{conn_id}')
            if delete_response:
                count += 1
                self.deleted_count += 1
                print(f"[SUCCESS] Deleted IdP: {conn_name}")
            else:
                self.failed_count += 1
                print(f"[FAILED] Could not delete IdP: {conn_name}")

            time.sleep(0.5)  # Rate limiting

        return count

    def delete_uem_connectors(self) -> int:
        """Delete all UEM connectors"""
        print("\n[DELETE] Fetching UEM connectors...")

        response = self._radar_request('GET', '/gate/connector-service/v2/config')
        if not response:
            return 0

        data = response.json()
        # The response has a "configs" array
        connectors = data.get('configs', []) if isinstance(data, dict) else data

        if not connectors:
            print("[INFO] No UEM connectors found")
            return 0

        count = 0
        for connector in connectors:
            conn_id = connector.get('id')
            conn_url = connector.get('url', 'Unknown')
            print(f"[DELETE] Deleting UEM connector: {conn_url} (ID: {conn_id})")

            delete_response = self._radar_request('DELETE', f'/gate/connector-service/v2/config/{conn_id}')
            if delete_response:
                count += 1
                self.deleted_count += 1
                print(f"[SUCCESS] Deleted UEM connector: {conn_url}")
            else:
                self.failed_count += 1
                print(f"[FAILED] Could not delete UEM connector: {conn_url}")

            time.sleep(0.5)

        return count

    def delete_ztna_policies(self) -> int:
        """Delete all ZTNA policies"""
        print("\n[DELETE] Fetching ZTNA policies...")

        response = self._radar_request('GET', '/api/app-definitions')
        if not response:
            print("[INFO] No ZTNA policies found (endpoint may not be available)")
            return 0

        policies = response.json()
        if not policies or not isinstance(policies, list):
            print("[INFO] No ZTNA policies found")
            return 0

        count = 0
        for policy in policies:
            if not isinstance(policy, dict):
                continue

            policy_id = policy.get('id')
            policy_name = policy.get('name', 'Unknown')

            if not policy_id:
                continue

            print(f"[DELETE] Deleting ZTNA policy: {policy_name} (ID: {policy_id})")

            delete_response = self._radar_request('DELETE', f'/api/app-definitions/{policy_id}')
            if delete_response:
                count += 1
                self.deleted_count += 1
                print(f"[SUCCESS] Deleted ZTNA policy: {policy_name}")
            else:
                self.failed_count += 1
                print(f"[FAILED] Could not delete ZTNA policy: {policy_name}")

            time.sleep(0.5)

        return count

    def delete_activation_profiles(self) -> int:
        """Delete all activation profiles"""
        print("\n[DELETE] Fetching activation profiles...")

        response = self._radar_request('GET', '/gate/activation-profile-service/v1/enrollment-links')
        if not response:
            return 0

        data = response.json()
        if not data:
            print("[INFO] No activation profiles found")
            return 0

        # The response might be:
        # 1. A list of profiles directly
        # 2. A dict with a field containing profiles (like {"links": [...]} or {"enrollmentLinks": [...]})
        # 3. A single profile dict
        profiles = []
        if isinstance(data, list):
            profiles = data
        elif isinstance(data, dict):
            # Try common field names for profile arrays
            profiles = data.get('links', data.get('enrollmentLinks', data.get('profiles', [])))
            # If it's still not a list, it might be a single profile
            if not isinstance(profiles, list):
                if data.get('code') or data.get('id'):
                    profiles = [data]

        if not profiles:
            print("[INFO] No activation profiles found")
            return 0

        count = 0
        for profile in profiles:
            # Skip if profile is not a dict (might be string or other type)
            if not isinstance(profile, dict):
                print(f"[WARN] Skipping non-dict profile: {profile}")
                continue

            profile_id = profile.get('code') or profile.get('id')
            profile_name = profile.get('name', 'Unknown')

            # Check if profile is already deleted or inactive
            # The management.effectiveState field indicates if already deleted
            management = profile.get('management', {})
            effective_state = management.get('effectiveState', '').upper()
            status = profile.get('status', '').upper()
            state = profile.get('state', '').upper()
            deleted = profile.get('deleted', False)

            if deleted or status == 'DELETED' or state == 'DELETED' or status == 'INACTIVE' or effective_state == 'DELETED':
                # Silently skip already-deleted profiles (common in API responses)
                continue

            if not profile_id:
                print(f"[WARN] Skipping profile without ID: {profile_name}")
                continue

            print(f"[DELETE] Deleting activation profile: {profile_name} (ID: {profile_id})")

            delete_response = self._radar_request('DELETE', f'/gate/activation-profile-service/v1/enrollment-links/{profile_id}')
            if delete_response:
                count += 1
                self.deleted_count += 1
                print(f"[SUCCESS] Deleted activation profile: {profile_name}")
            else:
                self.failed_count += 1
                print(f"[FAILED] Could not delete activation profile: {profile_name}")

            time.sleep(0.5)

        return count

    def delete_hostname_mappings(self) -> int:
        """Delete all hostname mappings"""
        print("\n[DELETE] Fetching hostname mappings...")

        response = self._radar_request('GET', '/gate/dns-zone-management-service/v1/custom-hostname-mappings')
        if not response:
            return 0

        data = response.json()

        # The response is {"mappings": [...]}
        if isinstance(data, dict):
            mappings = data.get('mappings', [])
        else:
            mappings = data if isinstance(data, list) else []

        if not mappings:
            print("[INFO] No hostname mappings found")
            return 0

        # Hostname mappings are managed as a collection, delete all at once
        print(f"[DELETE] Deleting {len(mappings)} hostname mapping(s)")

        # Send empty mappings array wrapped in proper structure
        delete_response = self._radar_request(
            'PUT',
            '/gate/dns-zone-management-service/v1/custom-hostname-mappings',
            json={"mappings": []}
        )

        if delete_response:
            count = len(mappings)
            self.deleted_count += count
            print(f"[SUCCESS] Deleted all hostname mappings")
            return count
        else:
            self.failed_count += len(mappings)
            print(f"[FAILED] Could not delete hostname mappings")
            return 0

    def reset_block_pages(self) -> int:
        """Reset block page customizations to defaults"""
        print("\n[DELETE] Resetting block page customizations...")

        # Block page is a singleton resource, we'll reset it to defaults
        # The API uses PATCH, so we'll send minimal data to reset

        default_block = {
            "description": "Default",
            "title": "",
            "showClassification": True,
            "showRequestUrl": True,
            "logo": ""
        }

        response = self._radar_request(
            'PATCH',
            f'/gate/block-service/blocks/v1/customers/{{customerid}}',
            json=default_block
        )

        if response:
            self.deleted_count += 1
            print("[SUCCESS] Reset block page to defaults")
            return 1
        else:
            self.failed_count += 1
            print("[FAILED] Could not reset block page")
            return 0

    def delete_pag_ztna_apps(self) -> int:
        """Delete all PAG ZTNA applications"""
        if not self.auth.pag_token:
            print("\n[SKIP] PAG not authenticated, skipping PAG ZTNA apps")
            return 0

        print("\n[DELETE] Fetching PAG ZTNA applications...")

        response = self._pag_request('GET', '/ztna/v1/apps')
        if not response:
            return 0

        apps = response.json()
        if not apps:
            print("[INFO] No PAG ZTNA apps found")
            return 0

        count = 0
        for app in apps:
            app_id = app.get('id')
            app_name = app.get('name', 'Unknown')
            print(f"[DELETE] Deleting PAG ZTNA app: {app_name} (ID: {app_id})")

            delete_response = self._pag_request('DELETE', f'/ztna/v1/apps/{app_id}')
            if delete_response:
                count += 1
                self.deleted_count += 1
                print(f"[SUCCESS] Deleted PAG ZTNA app: {app_name}")
            else:
                self.failed_count += 1
                print(f"[FAILED] Could not delete PAG ZTNA app: {app_name}")

            time.sleep(0.5)

        return count

    def delete_protect_prevent_lists(self) -> int:
        """Delete all Jamf Protect prevent lists"""
        if not self.auth.protect_token:
            print("\n[SKIP] Protect not authenticated, skipping prevent lists")
            return 0

        print("\n[DELETE] Fetching Jamf Protect prevent lists...")

        # GraphQL query to get all prevent lists
        query = """
        query {
            preventLists {
                id
                name
                type
            }
        }
        """

        response = self._protect_request(query)
        if not response or 'data' not in response:
            return 0

        prevent_lists = response.get('data', {}).get('preventLists', [])
        if not prevent_lists:
            print("[INFO] No Protect prevent lists found")
            return 0

        count = 0
        for plist in prevent_lists:
            list_id = plist.get('id')
            list_name = plist.get('name', 'Unknown')
            list_type = plist.get('type', 'Unknown')
            print(f"[DELETE] Deleting prevent list: {list_name} (Type: {list_type}, ID: {list_id})")

            # GraphQL mutation to delete prevent list
            delete_mutation = """
            mutation DeletePreventList($id: ID!) {
                deletePreventList(id: $id) {
                    success
                }
            }
            """

            delete_response = self._protect_request(delete_mutation, {'id': list_id})
            if delete_response and delete_response.get('data', {}).get('deletePreventList', {}).get('success'):
                count += 1
                self.deleted_count += 1
                print(f"[SUCCESS] Deleted prevent list: {list_name}")
            else:
                self.failed_count += 1
                print(f"[FAILED] Could not delete prevent list: {list_name}")

            time.sleep(0.5)

        return count

    def delete_all_resources(self, dry_run: bool = False, non_interactive: bool = False):
        """Delete all resources in proper order"""
        print("\n" + "="*70)
        print("JAMF SECURITY CLOUD - DELETE ALL RESOURCES")
        print("="*70)

        if dry_run:
            print("\n*** DRY RUN MODE - No resources will be deleted ***\n")
            return

        print("\n*** WARNING: This will delete ALL resources from your tenant ***")
        print("*** This operation CANNOT be undone ***\n")

        if not non_interactive:
            confirmation = input("Type 'DELETE ALL' to confirm: ")
            if confirmation != "DELETE ALL":
                print("\n[CANCELLED] Operation cancelled by user")
                return
        else:
            print("[INFO] Running in non-interactive mode (e.g., GitHub Actions)")
            print("[INFO] Confirmation has been pre-validated")

        print("\n[START] Beginning deletion process...\n")

        # Delete in dependency order
        # 1. Delete dependent resources first (ZTNA apps, activation profiles)
        self.delete_ztna_policies()
        self.delete_pag_ztna_apps()
        self.delete_activation_profiles()

        # 2. Delete hostname mappings
        self.delete_hostname_mappings()

        # 3. Reset block pages
        self.reset_block_pages()

        # 4. Delete connectors
        self.delete_uem_connectors()

        # 5. Delete IdPs last
        self.delete_okta_idps()

        # 6. Delete Protect prevent lists
        self.delete_protect_prevent_lists()

        # Summary
        print("\n" + "="*70)
        print("DELETION SUMMARY")
        print("="*70)
        print(f"Successfully deleted: {self.deleted_count} resource(s)")
        print(f"Failed to delete: {self.failed_count} resource(s)")
        print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Delete all resources from a Jamf Security Cloud tenant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Delete all resources (will prompt for confirmation)
  python delete_all_jsc_resources.py --domain radar.wandera.com --username admin@example.com --password mypass123

  # With customer ID specified
  python delete_all_jsc_resources.py --domain radar.wandera.com --username admin@example.com --password mypass123 --customer-id 12345

  # Include PAG resources
  python delete_all_jsc_resources.py --domain radar.wandera.com --username admin@example.com --password mypass123 \\
      --pag-app-id myappid --pag-app-secret mysecret

  # Include Protect resources
  python delete_all_jsc_resources.py --domain radar.wandera.com --username admin@example.com --password mypass123 \\
      --protect-domain mycompany.protect.jamfcloud.com --protect-client-id myclientid --protect-client-password mypass

Environment variables (can be used instead of CLI args):
  JSC_DOMAIN, JSC_USERNAME, JSC_PASSWORD, JSC_CUSTOMER_ID
  JSC_PAG_APP_ID, JSC_PAG_APP_SECRET
  JSC_PROTECT_DOMAIN, JSC_PROTECT_CLIENT_ID, JSC_PROTECT_CLIENT_PASSWORD
        """
    )

    # Radar API credentials
    parser.add_argument('--domain', default='radar.wandera.com',
                       help='JSC domain (default: radar.wandera.com)')
    parser.add_argument('--username', required=True,
                       help='JSC username (or set JSC_USERNAME env var)')
    parser.add_argument('--password', required=True,
                       help='JSC password (or set JSC_PASSWORD env var)')
    parser.add_argument('--customer-id',
                       help='Customer ID (auto-discovered if not provided)')

    # PAG credentials
    parser.add_argument('--pag-app-id',
                       help='PAG Application ID (optional)')
    parser.add_argument('--pag-app-secret',
                       help='PAG Application Secret (optional)')

    # Protect credentials
    parser.add_argument('--protect-domain',
                       help='Jamf Protect domain (optional, e.g., company.protect.jamfcloud.com)')
    parser.add_argument('--protect-client-id',
                       help='Jamf Protect client ID (optional)')
    parser.add_argument('--protect-client-password',
                       help='Jamf Protect client password (optional)')

    # Operation mode
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run without interactive confirmation (for CI/CD use)')

    args = parser.parse_args()

    # Create configuration
    config = JSCConfig(
        domain=args.domain,
        username=args.username,
        password=args.password,
        customer_id=args.customer_id,
        application_id=args.pag_app_id,
        application_secret=args.pag_app_secret,
        protect_domain=args.protect_domain,
        protect_client_id=args.protect_client_id,
        protect_client_password=args.protect_client_password
    )

    # Authenticate
    auth = JSCAuthenticator(config)

    if not auth.authenticate_radar():
        print("\n[ERROR] Failed to authenticate to Radar API. Exiting.")
        sys.exit(1)

    # PAG and Protect are optional
    auth.authenticate_pag()
    auth.authenticate_protect()

    # Delete resources
    deleter = JSCResourceDeleter(config, auth)
    deleter.delete_all_resources(dry_run=args.dry_run, non_interactive=args.non_interactive)


if __name__ == '__main__':
    main()
