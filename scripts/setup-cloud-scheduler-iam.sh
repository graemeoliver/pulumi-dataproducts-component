#!/bin/bash
#
# Setup IAM permissions for Cloud Scheduler to trigger Dataplex Datascans
#
# This script grants the necessary IAM roles to the service account used by
# Cloud Scheduler jobs to trigger Dataplex datascans.
#
# Prerequisites:
# - You must have roles/iam.securityAdmin or roles/owner on the project
# - The service account must already exist
#
# Usage:
#   ./setup-cloud-scheduler-iam.sh PROJECT_ID SERVICE_ACCOUNT_EMAIL
#
# Example:
#   ./setup-cloud-scheduler-iam.sh my-project-123 scheduler-sa@my-project-123.iam.gserviceaccount.com
#
# If you don't provide a service account email, the script will use the default
# compute service account for the project.
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check arguments
if [ $# -lt 1 ]; then
    print_error "Missing required argument: PROJECT_ID"
    echo ""
    echo "Usage: $0 PROJECT_ID [SERVICE_ACCOUNT_EMAIL]"
    echo ""
    echo "Example:"
    echo "  $0 my-project-123"
    echo "  $0 my-project-123 scheduler-sa@my-project-123.iam.gserviceaccount.com"
    exit 1
fi

PROJECT_ID="$1"

# Get project number
print_info "Getting project number for project: $PROJECT_ID"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

if [ -z "$PROJECT_NUMBER" ]; then
    print_error "Failed to get project number for project: $PROJECT_ID"
    print_error "Please verify the project ID and ensure you have access to it"
    exit 1
fi

print_info "Project number: $PROJECT_NUMBER"

# Determine service account email
if [ $# -ge 2 ]; then
    SERVICE_ACCOUNT="$2"
    print_info "Using provided service account: $SERVICE_ACCOUNT"
else
    # Use default compute service account
    SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
    print_warning "No service account provided, using default compute service account:"
    print_info "  $SERVICE_ACCOUNT"
fi

# Validate service account format
if [[ ! "$SERVICE_ACCOUNT" =~ ^[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.gserviceaccount\.com$ ]]; then
    print_error "Invalid service account email format: $SERVICE_ACCOUNT"
    print_error "Expected format: name@project-id.iam.gserviceaccount.com"
    exit 1
fi

echo ""
print_info "================================================================"
print_info "Setting up IAM for Cloud Scheduler → Dataplex Datascans"
print_info "================================================================"
echo ""
print_info "Project ID:          $PROJECT_ID"
print_info "Project Number:      $PROJECT_NUMBER"
print_info "Service Account:     $SERVICE_ACCOUNT"
echo ""

# Grant Dataplex Datascans Runner role
print_info "Granting roles/dataplex.datascans.runner to service account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/dataplex.datascans.runner" \
    --condition=None

if [ $? -eq 0 ]; then
    print_info "Successfully granted roles/dataplex.datascans.runner"
else
    print_error "Failed to grant roles/dataplex.datascans.runner"
    exit 1
fi

echo ""
print_info "================================================================"
print_info "IAM Setup Complete!"
print_info "================================================================"
echo ""
print_info "The service account can now trigger Dataplex datascans via Cloud Scheduler."
echo ""
print_info "Next steps:"
print_info "1. Deploy your Pulumi stack with useCloudSchedulerForScans=true"
print_info "2. Verify scheduler jobs are created: gcloud scheduler jobs list --location=<LOCATION>"
print_info "3. Test a manual run: gcloud scheduler jobs run <JOB_NAME> --location=<LOCATION>"
echo ""

# Optional: Verify the binding
print_info "Verifying IAM binding..."
BINDINGS=$(gcloud projects get-iam-policy "$PROJECT_ID" \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT AND bindings.role:roles/dataplex.datascans.runner")

if [[ "$BINDINGS" == *"roles/dataplex.datascans.runner"* ]]; then
    print_info "✓ Verified: Service account has roles/dataplex.datascans.runner"
else
    print_warning "Could not verify IAM binding. Please check manually:"
    print_warning "  gcloud projects get-iam-policy $PROJECT_ID --flatten=\"bindings[].members\" --filter=\"bindings.members:serviceAccount:$SERVICE_ACCOUNT\""
fi

echo ""
print_info "Done!"
