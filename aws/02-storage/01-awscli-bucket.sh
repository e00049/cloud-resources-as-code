#!/bin/bash

# Set strict mode for error handling
set -euo pipefail

# Function to show usage
usage() {
    echo "Usage: $0 <action> <bucket_name> <region>"
    echo "  action      - create, delete, or check"
    echo "  bucket_name - Name of the S3 bucket (e.g., my-bucket)"
    echo "  region      - AWS region (e.g., ap-south-1, us-east-1)"
    echo ""
    echo "Examples:"
    echo "  $0 create my-bucket ap-south-1"
    echo "  $0 delete my-bucket ap-south-1"
    echo "  $0 check my-bucket ap-south-1"
    exit 1
}

# Check if all required arguments are provided
if [ $# -ne 3 ]; then
    echo "Error: Missing required arguments"
    usage
fi

# Parse command line arguments
ACTION="$1"
BUCKET_NAME="$2"
REGION="$3"

# Debug print arguments
echo "Action: $ACTION"
echo "Bucket: s3://$BUCKET_NAME"
echo "Region: $REGION"
echo "------------------------"

# Function to check if bucket exists
bucket_exists() {
    if aws s3api head-bucket --bucket "${BUCKET_NAME}" --region "${REGION}" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to create bucket
create_bucket() {
    if bucket_exists; then
        echo "Bucket s3://${BUCKET_NAME} already exists. Skipping creation."
        return 0
    fi

    echo "Creating bucket s3://${BUCKET_NAME} in ${REGION}..."
    
    # For us-east-1, you don't specify LocationConstraint
    if [ "$REGION" = "us-east-1" ]; then
        if aws s3api create-bucket \
            --bucket "${BUCKET_NAME}" \
            --region "${REGION}"; then
            echo "✅ Successfully created bucket: s3://${BUCKET_NAME}"
        else
            echo "❌ Failed to create bucket: s3://${BUCKET_NAME}"
            exit 1
        fi
    else
        # For all other regions, specify LocationConstraint
        if aws s3api create-bucket \
            --bucket "${BUCKET_NAME}" \
            --region "${REGION}" \
            --create-bucket-configuration LocationConstraint="${REGION}"; then
            echo "✅ Successfully created bucket: s3://${BUCKET_NAME}"
        else
            echo "❌ Failed to create bucket: s3://${BUCKET_NAME}"
            exit 1
        fi
    fi
}

# Function to delete bucket (improved version)
delete_bucket() {
    if ! bucket_exists; then
        echo "Bucket s3://${BUCKET_NAME} does not exist. Skipping deletion."
        return 0
    fi

    echo "Deleting bucket s3://${BUCKET_NAME}..."
    
    # Try to empty the bucket first
    echo "Attempting to empty bucket contents..."
    if aws s3 rm "s3://${BUCKET_NAME}/" --recursive --quiet 2>/dev/null; then
        echo "Emptied bucket contents"
    else
        echo "Bucket is already empty or couldn't be emptied (continuing...)"
    fi

    # Delete the bucket
    if aws s3api delete-bucket \
        --bucket "${BUCKET_NAME}" \
        --region "${REGION}"; then
        echo "✅ Successfully deleted bucket: s3://${BUCKET_NAME}"
    else
        echo "❌ Failed to delete bucket: s3://${BUCKET_NAME}"
        exit 1
    fi
}

# Function to check bucket
check_bucket() {
    if bucket_exists; then
        echo "✅ Bucket s3://${BUCKET_NAME} exists"
        
        # Get additional bucket information
        echo "Bucket details:"
        aws s3api get-bucket-location --bucket "${BUCKET_NAME}" --output text 2>/dev/null | \
            awk '{print "   Region: " $1}'
        
        aws s3api get-bucket-creation-date --bucket "${BUCKET_NAME}" --output text 2>/dev/null | \
            awk '{print "   Created: " $1}'
        
        exit 0
    else
        echo "❌ Bucket s3://${BUCKET_NAME} does not exist"
        exit 1
    fi
}

# Function to list buckets (additional utility)
list_buckets() {
    echo "Listing all S3 buckets:"
    aws s3 ls
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
    list)
        list_buckets
        ;;
    *)
        echo "Error: Invalid action '${ACTION}'"
        usage
        ;;
esac

echo "Operation completed successfully"
