#!/bin/bash
#
# Test Data Quality Alerting Feature
#
# This script verifies that data quality alerts are properly configured
# after deploying a data product with alerting enabled.
#
# Usage:
#   ./test_dq_alerts.sh [PROJECT_ID] [DATA_PRODUCT_ID]
#
# Example:
#   ./test_dq_alerts.sh cubedev2-lab-1c497b test-data-product-001

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT="${1:-cubedev2-lab-1c497b}"
DATA_PRODUCT_ID="${2:-test-data-product-001}"
LOCATION="${3:-northamerica-northeast1}"

echo -e "${BLUE}=== Data Quality Alert Testing ===${NC}"
echo
echo "Project: $PROJECT"
echo "Data Product: $DATA_PRODUCT_ID"
echo "Location: $LOCATION"
echo

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -ne "${YELLOW}[TEST]${NC} $test_name... "

    if eval "$test_command" &>/dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test 1: Check if gcloud is installed
echo -e "\n${BLUE}[1/6] Environment Check${NC}"
run_test "gcloud CLI installed" "command -v gcloud"

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "\n${RED}ERROR: gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Test 2: Check notification channels
echo -e "\n${BLUE}[2/6] Notification Channels${NC}"

CHANNELS=$(gcloud alpha monitoring channels list \
    --project=$PROJECT \
    --filter="displayName:Data Quality" \
    --format="value(name)" 2>/dev/null || echo "")

if [ -z "$CHANNELS" ]; then
    echo -e "${RED}✗ FAIL${NC} No data quality notification channels found"
    ((TESTS_FAILED++))
else
    CHANNEL_COUNT=$(echo "$CHANNELS" | wc -l)
    echo -e "${GREEN}✓ PASS${NC} Found $CHANNEL_COUNT notification channel(s)"
    ((TESTS_PASSED++))

    # Show channel details
    echo -e "\n${YELLOW}Notification Channels:${NC}"
    gcloud alpha monitoring channels list \
        --project=$PROJECT \
        --filter="displayName:Data Quality" \
        --format="table(displayName,labels.email_address,enabled)" 2>/dev/null || true
fi

# Test 3: Check alert policies
echo -e "\n${BLUE}[3/6] Alert Policies${NC}"

POLICIES=$(gcloud alpha monitoring policies list \
    --project=$PROJECT \
    --filter="displayName:Data Quality" \
    --format="value(name)" 2>/dev/null || echo "")

if [ -z "$POLICIES" ]; then
    echo -e "${RED}✗ FAIL${NC} No data quality alert policies found"
    ((TESTS_FAILED++))
else
    POLICY_COUNT=$(echo "$POLICIES" | wc -l)

    # Should have 3 policies per dataset (Failure, Low Score, Stale)
    if [ "$POLICY_COUNT" -ge 3 ]; then
        echo -e "${GREEN}✓ PASS${NC} Found $POLICY_COUNT alert policies (expected >= 3)"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠ WARN${NC} Found only $POLICY_COUNT policies (expected >= 3)"
        ((TESTS_FAILED++))
    fi

    # Show policy summary
    echo -e "\n${YELLOW}Alert Policies:${NC}"
    gcloud alpha monitoring policies list \
        --project=$PROJECT \
        --filter="displayName:Data Quality" \
        --format="table(displayName,enabled)" 2>/dev/null | head -15 || true
fi

# Test 4: Verify policy types
echo -e "\n${BLUE}[4/6] Alert Policy Types${NC}"

POLICY_NAMES=$(gcloud alpha monitoring policies list \
    --project=$PROJECT \
    --filter="displayName:Data Quality" \
    --format="value(displayName)" 2>/dev/null || echo "")

HAS_FAILURE=$(echo "$POLICY_NAMES" | grep -i "failure" || echo "")
HAS_LOW_SCORE=$(echo "$POLICY_NAMES" | grep -i "low.*score" || echo "")
HAS_STALE=$(echo "$POLICY_NAMES" | grep -i "stale" || echo "")

if [ -n "$HAS_FAILURE" ]; then
    echo -e "${GREEN}✓ PASS${NC} Scan Failure alerts configured"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} Scan Failure alerts missing"
    ((TESTS_FAILED++))
fi

if [ -n "$HAS_LOW_SCORE" ]; then
    echo -e "${GREEN}✓ PASS${NC} Low Quality Score alerts configured"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} Low Quality Score alerts missing"
    ((TESTS_FAILED++))
fi

if [ -n "$HAS_STALE" ]; then
    echo -e "${GREEN}✓ PASS${NC} Scan Staleness alerts configured"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} Scan Staleness alerts missing"
    ((TESTS_FAILED++))
fi

# Test 5: Check DataScans
echo -e "\n${BLUE}[5/6] DataScans${NC}"

DATASCANS=$(gcloud dataplex datascans list \
    --location=$LOCATION \
    --project=$PROJECT \
    --filter="dataScanId:$DATA_PRODUCT_ID" \
    --format="value(name)" 2>/dev/null || echo "")

if [ -z "$DATASCANS" ]; then
    echo -e "${YELLOW}⚠ WARN${NC} No DataScans found for data product: $DATA_PRODUCT_ID"
    echo -e "         (This is OK if data quality scans are not enabled)"
else
    DATASCAN_COUNT=$(echo "$DATASCANS" | wc -l)
    echo -e "${GREEN}✓ PASS${NC} Found $DATASCAN_COUNT DataScan(s)"
    ((TESTS_PASSED++))

    # Show DataScan summary
    echo -e "\n${YELLOW}DataScans:${NC}"
    gcloud dataplex datascans list \
        --location=$LOCATION \
        --project=$PROJECT \
        --filter="dataScanId:$DATA_PRODUCT_ID" \
        --format="table(dataScanId,type,state)" 2>/dev/null || true
fi

# Test 6: Check for active incidents
echo -e "\n${BLUE}[6/6] Active Incidents${NC}"

INCIDENTS=$(gcloud alpha monitoring policies incidents list \
    --project=$PROJECT \
    --filter="state=OPEN AND policyName:Data Quality" \
    --format="value(name)" 2>/dev/null || echo "")

if [ -z "$INCIDENTS" ]; then
    echo -e "${GREEN}✓ PASS${NC} No active incidents (all alerts healthy)"
    ((TESTS_PASSED++))
else
    INCIDENT_COUNT=$(echo "$INCIDENTS" | wc -l)
    echo -e "${YELLOW}⚠ INFO${NC} $INCIDENT_COUNT active incident(s) found"

    # Show incident details
    echo -e "\n${YELLOW}Active Incidents:${NC}"
    gcloud alpha monitoring policies incidents list \
        --project=$PROJECT \
        --filter="state=OPEN AND policyName:Data Quality" \
        --format="table(name,startTime,policyName)" 2>/dev/null || true
fi

# Summary
echo
echo -e "${BLUE}=== Test Summary ===${NC}"
echo
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo
    echo "Next steps:"
    echo "1. Test triggering an alert (see TESTING-DATA-QUALITY-ALERTS.md)"
    echo "2. Verify email notifications are received"
    echo "3. Check that links in emails work correctly"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo
    echo "Possible causes:"
    echo "1. Data quality alerts not enabled in Pulumi configuration"
    echo "2. Alert email not configured"
    echo "3. Resources not yet created (deployment still in progress)"
    echo "4. Wrong project ID or data product ID"
    echo
    echo "To enable alerts, add to your Pulumi config:"
    echo "  enableDataQualityScans: true"
    echo "  dataQualityAlertEmail: \"your-email@company.com\""
    exit 1
fi
