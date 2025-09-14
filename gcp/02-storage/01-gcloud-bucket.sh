#!/bin/bash

# Set strict mode for error handling
set -euo pipefail

# Function to show usage
usage() {
    echo "Usage: $0 <action> <bucket_name> <location> <project_id>"
    echo "  action      - create, delete, or check"
    echo "  bucket_name - Name of the GCS bucket (e.g., my-bucket)"
    echo "  location    - GCS location (e.g., asia-south1, us-central1)"
    echo "  project_id  - Google Cloud project ID"
    echo ""
    echo "Examples:"
    echo "  $0 create my-bucket asia-south1 my-project-id"
    echo "  $0 delete my-bucket asia-south1 my-project-id"
    echo "  $0 check my-bucket asia-south1 my-project-id"
    exit 1
}

# Check if all required arguments are provided
if [ $# -ne 4 ]; then
    echo "Error: Missing required arguments"
    usage
fi

# Parse command line arguments
ACTION="$1"
BUCKET_NAME="$2"
LOCATION="$3"
PROJECT_ID="$4"
STORAGE_CLASS="STANDARD"  # Default value, can be made configurable too

# Debug print arguments
echo "Action: $ACTION"
echo "Bucket: gs://$BUCKET_NAME"
echo "Location: $LOCATION"
echo "Project: $PROJECT_ID"
echo "------------------------"

# Function to check if bucket exists
bucket_exists() {
    if gcloud storage buckets describe "gs://${BUCKET_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to create bucket
create_bucket() {
    if bucket_exists; then
        echo "Bucket gs://${BUCKET_NAME} already exists. Skipping creation."
        return 0
    fi

    echo "Creating bucket gs://${BUCKET_NAME} in ${LOCATION}..."
    if gcloud storage buckets create "gs://${BUCKET_NAME}" \
        --location="${LOCATION}" \
        --default-storage-class="${STORAGE_CLASS}" \
        --project="${PROJECT_ID}"; then
        echo "✅ Successfully created bucket: gs://${BUCKET_NAME}"
    else
        echo "❌ Failed to create bucket: gs://${BUCKET_NAME}"
        exit 1
    fi
}

# Function to delete bucket (improved version)
delete_bucket() {
    if ! bucket_exists; then
        echo "Bucket gs://${BUCKET_NAME} does not exist. Skipping deletion."
        return 0
    fi

    echo "Deleting bucket gs://${BUCKET_NAME}..."
    
    # Try to empty the bucket (but don't fail if it's already empty)
    echo "Attempting to empty bucket contents..."
    if gcloud storage rm "gs://${BUCKET_NAME}/**" --recursive --quiet 2>/dev/null; then
        echo "Emptied bucket contents"
    else
        echo "Bucket is already empty or couldn't be emptied (continuing...)"
    fi

    if gcloud storage buckets delete "gs://${BUCKET_NAME}" \
        --project="${PROJECT_ID}" \
        --quiet; then
        echo "✅ Successfully deleted bucket: gs://${BUCKET_NAME}"
    else
        echo "❌ Failed to delete bucket: gs://${BUCKET_NAME}"
        exit 1
    fi
}

# Function to check bucket
check_bucket() {
    if bucket_exists; then
        echo "✅ Bucket gs://${BUCKET_NAME} exists"
        exit 0
    else
        echo "❌ Bucket gs://${BUCKET_NAME} does not exist"
        exit 1
    fi
}

# Main execution
case "${ACTION}" in
    create)
        create_bucket
        ;;
    delete)
        delete_bucket
        ;;
    check)
        check_bucket
        ;;
    *)
        echo "Error: Invalid action '${ACTION}'"
        usage
        ;;
esac

echo "Operation completed successfully"
