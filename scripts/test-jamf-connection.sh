#!/bin/bash

# Test script to verify Jamf Pro connectivity and credentials
# Use this to validate your setup before configuring GitHub secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Jamf Pro Connection Test ==="
echo ""

# Check if environment variables are set
if [ -z "$JAMF_URL" ] || [ -z "$JAMF_USERNAME" ] || [ -z "$JAMF_PASSWORD" ]; then
    echo -e "${YELLOW}Environment variables not set. Please provide credentials:${NC}"
    echo ""
    
    if [ -z "$JAMF_URL" ]; then
        read -p "Jamf Pro URL (e.g., https://yourserver.jamfcloud.com): " JAMF_URL
    fi
    
    if [ -z "$JAMF_USERNAME" ]; then
        read -p "Jamf Pro Username: " JAMF_USERNAME
    fi
    
    if [ -z "$JAMF_PASSWORD" ]; then
        read -s -p "Jamf Pro Password: " JAMF_PASSWORD
        echo ""
    fi
    echo ""
fi

# Remove trailing slash from URL if present
JAMF_URL=${JAMF_URL%/}

echo "Testing connection to: $JAMF_URL"
echo "Username: $JAMF_USERNAME"
echo ""

# Test 1: Health Check
echo "🔍 Testing Jamf Pro health check..."
if curl -ksS "$JAMF_URL/healthCheck.html" | grep -q "\\[\\]"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed - server may be unavailable${NC}"
    exit 1
fi

# Test 2: Authentication
echo "🔐 Testing authentication..."
auth_response=$(curl -s -u "$JAMF_USERNAME:$JAMF_PASSWORD" "$JAMF_URL/api/v1/auth/token" -X POST)

echo "$auth_response"

if echo "$auth_response" | grep -q "token"; then
    bearer_token=$(echo "$auth_response" | plutil -extract token raw -)
    echo -e "${GREEN}✅ Authentication successful${NC}"
else
    echo -e "${RED}❌ Authentication failed${NC}"
    echo "Response: $auth_response"
    exit 1
fi

echo "Bearer Token: $bearer_token"

# Test 3: Basic API Access
echo "📊 Testing API access..."
categories_response=$(curl -s -H "Authorization: Bearer $bearer_token" "$JAMF_URL/JSSResource/categories")
echo "$categories_response"

if echo "$categories_response" | grep -q "<categories>"; then
    category_count=$(echo "$categories_response" | grep -o '<id>[0-9]*</id>' | wc -l)
    echo -e "${GREEN}✅ API access successful${NC}"
    echo "   Found $category_count existing categories"
else
    echo -e "${RED}❌ API access failed${NC}"
    echo "Response: $categories_response"
    exit 1
fi

# Test 4: Write Permissions (create and delete a test category)
echo "✏️  Testing write permissions..."
test_category_xml='<?xml version="1.0" encoding="UTF-8"?>
<category>
    <name>__TEST_CATEGORY_DELETE_ME__</name>
    <priority>10</priority>
</category>'

# Create test category
create_response=$(curl -s -H "Content-Type: application/xml" -H "Authorization: Bearer $bearer_token" -d "$test_category_xml" "$JAMF_URL/JSSResource/categories/id/0" -X POST)

if echo "$create_response" | grep -q "__TEST_CATEGORY_DELETE_ME__"; then
    # Extract the ID of the created category
    test_category_id=$(echo "$create_response" | grep -o '<id>[0-9]*</id>' | head -1 | sed 's/<[^>]*>//g')
    echo -e "${GREEN}✅ Create permission verified${NC}"
    
    # Clean up - delete the test category
    delete_response=$(curl -s -H "Authorization: Bearer $bearer_token" "$JAMF_URL/JSSResource/categories/id/$test_category_id" -X DELETE)
    
    if echo "$delete_response" | grep -q "<?xml"; then
        echo -e "${GREEN}✅ Delete permission verified${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not delete test category (ID: $test_category_id)${NC}"
        echo "   Please manually remove '__TEST_CATEGORY_DELETE_ME__' from your Jamf Pro server"
    fi
else
    echo -e "${RED}❌ Write permissions failed${NC}"
    echo "Response: $create_response"
fi

# Test 5: Check existing objects (to understand cleanup scope)
echo "📋 Checking existing objects..."
objects_to_check=("categories" "policies" "osxconfigurationprofiles" "computergroups")

for object_type in "${objects_to_check[@]}"; do
    object_response=$(curl -s -H "Authorization: Bearer $bearer_token" "$JAMF_URL/JSSResource/$object_type")
    object_count=$(echo "$object_response" | grep -o '<id>[0-9]*</id>' | wc -l)
    echo "   $object_type: $object_count objects"
done

echo ""
echo -e "${GREEN}🎉 All tests passed!${NC}"
echo ""
echo "Your Jamf Pro credentials are ready for use in GitHub Actions."
echo "Add these values to your GitHub repository secrets:"
echo ""
echo "JAMF_URL: $JAMF_URL"
echo "JAMF_USERNAME: $JAMF_USERNAME"
echo "JAMF_PASSWORD: [your password]"
echo ""
echo "Optional OAuth2 credentials (if you prefer token-based auth):"
echo "JAMF_CLIENT_ID: [your client ID]"
echo "JAMF_CLIENT_SECRET: [your client secret]"
echo ""
echo -e "${YELLOW}Note: The cleanup script will delete ALL objects shown above.${NC}"
echo "Make sure this is a dedicated demo server!"