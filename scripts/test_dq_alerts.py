#!/usr/bin/env python3
"""
Test Data Quality Alerting Feature

This script verifies that data quality alerts are properly configured.

Usage:
    python test_dq_alerts.py [--project PROJECT] [--data-product-id ID]

Example:
    python test_dq_alerts.py --project cubedev2-lab-1c497b --data-product-id test-data-product-001
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, List, Optional


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class TestResult:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def pass_test(self):
        self.passed += 1

    def fail_test(self):
        self.failed += 1

    def warn_test(self):
        self.warnings += 1

    def all_passed(self) -> bool:
        return self.failed == 0


def run_gcloud(args: List[str], format_json: bool = True) -> Optional[List[Dict]]:
    """Run gcloud command and return output."""
    # On Windows, use gcloud.cmd
    if sys.platform == "win32":
        cmd = ["gcloud.cmd"] + args
    else:
        cmd = ["gcloud"] + args

    if format_json:
        cmd += ["--format=json"]

    print(f"  Running: {' '.join(cmd[:4])}...", end=" ", flush=True)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30  # 30 second timeout
        )
        print("done")
        if format_json:
            return json.loads(result.stdout) if result.stdout else []
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}TIMEOUT{Colors.NC}")
        print(f"{Colors.YELLOW}  Command timed out after 30 seconds{Colors.NC}")
        return None
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}FAILED{Colors.NC}")
        print(f"{Colors.YELLOW}  Error: {e.stderr[:200]}{Colors.NC}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"{Colors.RED}ERROR{Colors.NC}")
        print(f"{Colors.YELLOW}  Unexpected error: {str(e)[:200]}{Colors.NC}", file=sys.stderr)
        return None


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.BLUE}{text}{Colors.NC}")


def print_pass(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ PASS{Colors.NC} {text}")


def print_fail(text: str):
    """Print failure message."""
    print(f"{Colors.RED}✗ FAIL{Colors.NC} {text}")


def print_warn(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ WARN{Colors.NC} {text}")


def test_notification_channels(project: str, results: TestResult):
    """Test that notification channels are created."""
    print_header("[1/5] Testing Notification Channels")

    channels = run_gcloud([
        "alpha", "monitoring", "channels", "list",
        f"--project={project}",
        "--filter=displayName:Data Quality"
    ])

    if channels is None or len(channels) == 0:
        print_fail("No data quality notification channels found")
        results.fail_test()
        return

    print_pass(f"Found {len(channels)} notification channel(s)")
    results.pass_test()

    # Verify channel details
    for channel in channels:
        display_name = channel.get("displayName", "Unknown")
        email = channel.get("labels", {}).get("email_address", "Not set")
        enabled = channel.get("enabled", False)

        print(f"  - {display_name}")
        print(f"    Email: {email}")
        print(f"    Enabled: {enabled}")

        if not enabled:
            print_warn(f"Channel '{display_name}' is disabled")
            results.warn_test()


def test_alert_policies(project: str, results: TestResult):
    """Test that alert policies are created."""
    print_header("[2/5] Testing Alert Policies")

    policies = run_gcloud([
        "alpha", "monitoring", "policies", "list",
        f"--project={project}",
        "--filter=displayName:Data Quality"
    ])

    if policies is None or len(policies) == 0:
        print_fail("No data quality alert policies found")
        results.fail_test()
        return

    # Should have at least 3 policies (Failure, Low Score, Stale)
    if len(policies) >= 3:
        print_pass(f"Found {len(policies)} alert policies (expected >= 3)")
        results.pass_test()
    else:
        print_warn(f"Found only {len(policies)} policies (expected >= 3)")
        results.warn_test()

    # Show policy summary
    print("\n  Alert Policies:")
    for policy in policies[:10]:  # Show first 10
        display_name = policy.get("displayName", "Unknown")
        enabled = policy.get("enabled", False)
        channels = len(policy.get("notificationChannels", []))

        status = "✓" if enabled else "✗"
        print(f"  {status} {display_name} ({channels} channel(s))")

        if not enabled:
            print_warn(f"Policy '{display_name}' is disabled")
            results.warn_test()


def test_policy_types(project: str, results: TestResult):
    """Test that all required policy types exist."""
    print_header("[3/5] Testing Policy Types")

    policies = run_gcloud([
        "alpha", "monitoring", "policies", "list",
        f"--project={project}",
        "--filter=displayName:Data Quality"
    ])

    if policies is None:
        print_fail("Could not retrieve policies")
        results.fail_test()
        return

    policy_names = [p.get("displayName", "").lower() for p in policies]

    # Check for required policy types
    has_failure = any("failure" in name for name in policy_names)
    has_low_score = any("low" in name and "score" in name for name in policy_names)
    has_stale = any("stale" in name for name in policy_names)

    if has_failure:
        print_pass("Scan Failure alerts configured")
        results.pass_test()
    else:
        print_fail("Scan Failure alerts missing")
        results.fail_test()

    if has_low_score:
        print_pass("Low Quality Score alerts configured")
        results.pass_test()
    else:
        print_fail("Low Quality Score alerts missing")
        results.fail_test()

    if has_stale:
        print_pass("Scan Staleness alerts configured")
        results.pass_test()
    else:
        print_fail("Scan Staleness alerts missing")
        results.fail_test()


def test_datascans(project: str, location: str, data_product_id: str, results: TestResult):
    """Test that DataScans exist."""
    print_header("[4/5] Testing DataScans")

    datascans = run_gcloud([
        "dataplex", "datascans", "list",
        f"--location={location}",
        f"--project={project}",
        f"--filter=dataScanId:{data_product_id}"
    ])

    if datascans is None or len(datascans) == 0:
        print_warn(f"No DataScans found for data product: {data_product_id}")
        print("         (This is OK if data quality scans are not enabled)")
        return

    print_pass(f"Found {len(datascans)} DataScan(s)")
    results.pass_test()

    # Show DataScan summary
    print("\n  DataScans:")
    for scan in datascans:
        scan_id = scan.get("name", "").split("/")[-1]
        scan_type = scan.get("type", "Unknown")
        state = scan.get("state", "Unknown")

        print(f"  - {scan_id}")
        print(f"    Type: {scan_type}")
        print(f"    State: {state}")


def test_incidents(project: str, results: TestResult):
    """Test for active incidents."""
    print_header("[5/5] Testing Active Incidents")

    incidents = run_gcloud([
        "alpha", "monitoring", "policies", "incidents", "list",
        f"--project={project}",
        "--filter=state=OPEN AND policyName:Data Quality"
    ])

    if incidents is None or len(incidents) == 0:
        print_pass("No active incidents (all alerts healthy)")
        results.pass_test()
        return

    print_warn(f"{len(incidents)} active incident(s) found")
    results.warn_test()

    # Show incident summary
    print("\n  Active Incidents:")
    for incident in incidents[:5]:  # Show first 5
        name = incident.get("name", "").split("/")[-1]
        start = incident.get("startTime", "Unknown")
        policy = incident.get("policyName", "").split("/")[-1]

        print(f"  - {name}")
        print(f"    Started: {start}")
        print(f"    Policy: {policy}")


def main():
    parser = argparse.ArgumentParser(
        description="Test data quality alerting configuration"
    )
    parser.add_argument(
        "--project",
        default="cubedev2-lab-1c497b",
        help="GCP project ID"
    )
    parser.add_argument(
        "--data-product-id",
        default="test-data-product-001",
        help="Data product ID"
    )
    parser.add_argument(
        "--location",
        default="northamerica-northeast1",
        help="GCP location"
    )

    args = parser.parse_args()

    print(f"{Colors.BLUE}=== Data Quality Alert Testing ==={Colors.NC}")
    print(f"\nProject: {args.project}")
    print(f"Data Product: {args.data_product_id}")
    print(f"Location: {args.location}")

    results = TestResult()

    # Run tests
    test_notification_channels(args.project, results)
    test_alert_policies(args.project, results)
    test_policy_types(args.project, results)
    test_datascans(args.project, args.location, args.data_product_id, results)
    test_incidents(args.project, results)

    # Summary
    print(f"\n{Colors.BLUE}=== Test Summary ==={Colors.NC}\n")
    print(f"Tests Passed:  {Colors.GREEN}{results.passed}{Colors.NC}")
    print(f"Tests Failed:  {Colors.RED}{results.failed}{Colors.NC}")
    print(f"Warnings:      {Colors.YELLOW}{results.warnings}{Colors.NC}\n")

    if results.all_passed():
        print(f"{Colors.GREEN}✓ All tests passed!{Colors.NC}\n")
        print("Next steps:")
        print("1. Test triggering an alert (see TESTING-DATA-QUALITY-ALERTS.md)")
        print("2. Verify email notifications are received")
        print("3. Check that links in emails work correctly")
        sys.exit(0)
    else:
        print(f"{Colors.RED}✗ Some tests failed{Colors.NC}\n")
        print("Possible causes:")
        print("1. Data quality alerts not enabled in Pulumi configuration")
        print("2. Alert email not configured")
        print("3. Resources not yet created (deployment still in progress)")
        print("4. Wrong project ID or data product ID\n")
        print("To enable alerts, add to your Pulumi config:")
        print("  enableDataQualityScans: true")
        print("  dataQualityAlertEmail: \"your-email@company.com\"")
        sys.exit(1)


if __name__ == "__main__":
    main()
