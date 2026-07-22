# Test Data Quality Alerts
# Usage: .\test_alerts.ps1 [ProjectId] [DataProductId]

param(
    [string]$ProjectId = "cubedev2-lab-1c497b",
    [string]$DataProductId = "test-data-product-001",
    [string]$Location = "northamerica-northeast1"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Data Quality Alert Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project: $ProjectId"
Write-Host "Data Product: $DataProductId"
Write-Host "Location: $Location"
Write-Host ""

$passed = 0
$failed = 0

# Test 1: Check notification channels
Write-Host "[1/5] Checking Notification Channels..." -ForegroundColor Blue
try {
    $channels = gcloud alpha monitoring channels list --project=$ProjectId --filter="displayName:Data Quality" --format=json 2>&1 | ConvertFrom-Json

    if ($channels.Count -gt 0) {
        Write-Host "  [PASS] Found $($channels.Count) notification channel(s)" -ForegroundColor Green
        $passed++

        foreach ($channel in $channels) {
            $email = $channel.labels.email_address
            $enabled = $channel.enabled
            Write-Host "    Email: $email (Enabled: $enabled)"
        }
    } else {
        Write-Host "  [FAIL] No notification channels found" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  [FAIL] Error checking channels: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Test 2: Check alert policies
Write-Host ""
Write-Host "[2/5] Checking Alert Policies..." -ForegroundColor Blue
try {
    $policies = gcloud alpha monitoring policies list --project=$ProjectId --filter="displayName:Data Quality" --format=json 2>&1 | ConvertFrom-Json

    if ($policies.Count -ge 3) {
        Write-Host "  [PASS] Found $($policies.Count) alert policies (expected >= 3)" -ForegroundColor Green
        $passed++
    } elseif ($policies.Count -gt 0) {
        Write-Host "  [WARN] Found only $($policies.Count) policies (expected >= 3)" -ForegroundColor Yellow
        $failed++
    } else {
        Write-Host "  [FAIL] No alert policies found" -ForegroundColor Red
        $failed++
    }

    if ($policies.Count -gt 0) {
        Write-Host ""
        Write-Host "  Alert Policies:" -ForegroundColor Yellow
        foreach ($policy in $policies | Select-Object -First 5) {
            $name = $policy.displayName
            $enabled = $policy.enabled
            $status = if ($enabled) { "[+]" } else { "[-]" }
            Write-Host "    $status $name"
        }
    }
} catch {
    Write-Host "  [FAIL] Error checking policies: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Test 3: Check policy types
Write-Host ""
Write-Host "[3/5] Checking Policy Types..." -ForegroundColor Blue
try {
    $policyNames = $policies | ForEach-Object { $_.displayName.ToLower() }

    $hasFailure = $policyNames | Where-Object { $_ -like "*failure*" }
    $hasLowScore = $policyNames | Where-Object { $_ -like "*low*score*" }
    $hasStale = $policyNames | Where-Object { $_ -like "*stale*" }

    $typeTests = 0
    if ($hasFailure) {
        Write-Host "  [PASS] Scan Failure alerts configured" -ForegroundColor Green
        $typeTests++
    } else {
        Write-Host "  [FAIL] Scan Failure alerts missing" -ForegroundColor Red
    }

    if ($hasLowScore) {
        Write-Host "  [PASS] Low Quality Score alerts configured" -ForegroundColor Green
        $typeTests++
    } else {
        Write-Host "  [FAIL] Low Quality Score alerts missing" -ForegroundColor Red
    }

    if ($hasStale) {
        Write-Host "  [PASS] Scan Staleness alerts configured" -ForegroundColor Green
        $typeTests++
    } else {
        Write-Host "  [FAIL] Scan Staleness alerts missing" -ForegroundColor Red
    }

    if ($typeTests -eq 3) { $passed++ } else { $failed++ }
} catch {
    Write-Host "  [FAIL] Error checking policy types" -ForegroundColor Red
    $failed++
}

# Test 4: Check DataScans
Write-Host ""
Write-Host "[4/5] Checking DataScans..." -ForegroundColor Blue
try {
    $datascans = gcloud dataplex datascans list --location=$Location --project=$ProjectId --filter="dataScanId:$DataProductId" --format=json 2>&1 | ConvertFrom-Json

    if ($datascans.Count -gt 0) {
        Write-Host "  [PASS] Found $($datascans.Count) DataScan(s)" -ForegroundColor Green
        $passed++

        Write-Host ""
        Write-Host "  DataScans:" -ForegroundColor Yellow
        foreach ($scan in $datascans | Select-Object -First 5) {
            $scanId = $scan.name.Split('/')[-1]
            $type = $scan.type
            $state = $scan.state
            Write-Host "    - $scanId ($type) - $state"
        }
    } else {
        Write-Host "  [INFO] No DataScans found (OK if DQ scans not enabled)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [WARN] Error checking DataScans: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Test 5: Check active incidents
Write-Host ""
Write-Host "[5/5] Checking Active Incidents..." -ForegroundColor Blue
try {
    $incidents = gcloud alpha monitoring policies incidents list --project=$ProjectId --filter="state=OPEN AND policyName:Data Quality" --format=json 2>&1 | ConvertFrom-Json

    if ($incidents.Count -eq 0 -or $null -eq $incidents) {
        Write-Host "  [PASS] No active incidents (all alerts healthy)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  [INFO] $($incidents.Count) active incident(s) found" -ForegroundColor Yellow

        Write-Host ""
        Write-Host "  Active Incidents:" -ForegroundColor Yellow
        foreach ($incident in $incidents | Select-Object -First 5) {
            $incidentId = $incident.name.Split('/')[-1]
            $startTime = $incident.startTime
            Write-Host "    - $incidentId (started: $startTime)"
        }
    }
} catch {
    Write-Host "  [WARN] Error checking incidents: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tests Passed: " -NoNewline
Write-Host "$passed" -ForegroundColor Green
Write-Host "Tests Failed: " -NoNewline
Write-Host "$failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "[PASS] All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Test triggering an alert (see TESTING-DATA-QUALITY-ALERTS.md)"
    Write-Host "2. Verify email notifications are received"
    Write-Host "3. Check that links in emails work correctly"
    exit 0
} else {
    Write-Host "[FAIL] Some tests failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible causes:"
    Write-Host "1. Data quality alerts not enabled in Pulumi configuration"
    Write-Host "2. Alert email not configured"
    Write-Host "3. Resources not yet created (deployment still in progress)"
    Write-Host ""
    Write-Host "To enable alerts, add to your Pulumi config:"
    Write-Host '  enableDataQualityScans: true'
    Write-Host '  dataQualityAlertEmail: "your-email@company.com"'
    exit 1
}
