@echo off
REM Quick check for data quality alerts
REM Usage: quick_check_alerts.bat [PROJECT_ID]

SET PROJECT=%1
IF "%PROJECT%"=="" SET PROJECT=cubedev2-lab-1c497b

echo ========================================
echo Data Quality Alerts Quick Check
echo ========================================
echo Project: %PROJECT%
echo.

echo [1/3] Checking notification channels...
gcloud alpha monitoring channels list --project=%PROJECT% --filter="displayName:Data Quality" --format="table(displayName,labels.email_address,enabled)" --limit=10
echo.

echo [2/3] Checking alert policies...
gcloud alpha monitoring policies list --project=%PROJECT% --filter="displayName:Data Quality" --format="table(displayName,enabled)" --limit=10
echo.

echo [3/3] Checking active incidents...
gcloud alpha monitoring policies incidents list --project=%PROJECT% --filter="state=OPEN AND policyName:Data Quality" --format="table(name,startTime,policyName)" --limit=10
echo.

echo ========================================
echo Check complete!
echo ========================================
