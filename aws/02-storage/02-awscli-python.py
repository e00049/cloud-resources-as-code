#!/usr/bin/env python3
"""
AWS S3 Bucket Management using Python Boto3
Usage: python3 script.py <action> <bucket_name> <region>
"""

import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def usage():
    """Show usage information"""
    print("Usage: python3 script.py <action> <bucket_name> <region>")
    print("  action      - create, delete, check, or list")
    print("  bucket_name - Name of the S3 bucket (e.g., my-bucket)")
    print("  region      - AWS region (e.g., ap-south-1, us-east-1)")
    print("")
    print("Examples:")
    print("  python3 script.py create my-bucket ap-south-1")
    print("  python3 script.py delete my-bucket ap-south-1")
    print("  python3 script.py check my-bucket ap-south-1")
    print("  python3 script.py list")
    sys.exit(1)

def create_s3_client(region):
    """Create and return an S3 client"""
    try:
        return boto3.client('s3', region_name=region)
    except NoCredentialsError:
        print("❌ AWS credentials not found. Configure with 'aws configure'")
        sys.exit(1)

def bucket_exists(s3_client, bucket_name):
    """Check if a bucket exists"""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            return False
        elif error_code == '403':
            print("❌ Access denied to bucket. Check permissions.")
            sys.exit(1)
        else:
            print(f"❌ Error checking bucket: {e}")
            sys.exit(1)

def create_bucket(s3_client, bucket_name, region):
    """Create an S3 bucket"""
    if bucket_exists(s3_client, bucket_name):
        print(f"Bucket s3://{bucket_name} already exists. Skipping creation.")
        return True
    
    print(f"Creating bucket s3://{bucket_name} in {region}...")
    
    try:
        if region == 'us-east-1':
            # us-east-1 is the default region
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            # All other regions require LocationConstraint
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"✅ Successfully created bucket: s3://{bucket_name}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'BucketAlreadyExists':
            print(f"Bucket s3://{bucket_name} already exists (different region).")
            return True
        elif error_code == 'BucketAlreadyOwnedByYou':
            print(f"Bucket s3://{bucket_name} already owned by you.")
            return True
        else:
            print(f"❌ Failed to create bucket: {e}")
            return False

def delete_bucket(s3_client, bucket_name, region):
    """Delete an S3 bucket"""
    if not bucket_exists(s3_client, bucket_name):
        print(f"Bucket s3://{bucket_name} does not exist. Skipping deletion.")
        return True
    
    print(f"Deleting bucket s3://{bucket_name}...")
    
    # Try to empty the bucket first
    try:
        print("Attempting to empty bucket contents...")
        s3_resource = boto3.resource('s3', region_name=region)
        bucket = s3_resource.Bucket(bucket_name)
        bucket.objects.all().delete()
        print("Emptied bucket contents")
    except ClientError as e:
        print(f"Bucket is already empty or couldn't be emptied: {e}")
    
    # Delete the bucket
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
        print(f"✅ Successfully deleted bucket: s3://{bucket_name}")
        return True
    except ClientError as e:
        print(f"❌ Failed to delete bucket: {e}")
        return False

def check_bucket(s3_client, bucket_name):
    """Check bucket existence and details"""
    if bucket_exists(s3_client, bucket_name):
        print(f"✅ Bucket s3://{bucket_name} exists")
        
        # Get bucket details
        try:
            location = s3_client.get_bucket_location(Bucket=bucket_name)
            region = location.get('LocationConstraint', 'us-east-1')
            print(f"   Region: {region}")
            
            # Get creation date (requires list_buckets)
            response = s3_client.list_buckets()
            for bucket in response['Buckets']:
                if bucket['Name'] == bucket_name:
                    print(f"   Created: {bucket['CreationDate']}")
                    break
                    
        except ClientError as e:
            print(f"   Could not retrieve details: {e}")
            
        return True
    else:
        print(f"❌ Bucket s3://{bucket_name} does not exist")
        return False

def list_buckets(s3_client):
    """List all S3 buckets"""
    print("Listing all S3 buckets:")
    try:
        response = s3_client.list_buckets()
        if not response['Buckets']:
            print("   No buckets found")
        else:
            for bucket in response['Buckets']:
                print(f"   {bucket['Name']} - Created: {bucket['CreationDate']}")
        return True
    except ClientError as e:
        print(f"❌ Failed to list buckets: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) not in [2, 4]:
        usage()
    
    action = sys.argv[1]
    
    # Handle list action (no bucket name needed)
    if action == 'list' and len(sys.argv) == 2:
        s3_client = create_s3_client('us-east-1')  # Default region for list
        success = list_buckets(s3_client)
        sys.exit(0 if success else 1)
    
    # Handle other actions (require bucket name and region)
    if len(sys.argv) != 4:
        usage()
    
    bucket_name = sys.argv[2]
    region = sys.argv[3]
    
    print(f"Action: {action}")
    print(f"Bucket: s3://{bucket_name}")
    print(f"Region: {region}")
    print("------------------------")
    
    s3_client = create_s3_client(region)
    success = False
    
    try:
        if action == 'create':
            success = create_bucket(s3_client, bucket_name, region)
        elif action == 'delete':
            success = delete_bucket(s3_client, bucket_name, region)
        elif action == 'check':
            success = check_bucket(s3_client, bucket_name)
        else:
            print(f"Error: Invalid action '{action}'")
            usage()
        
        if success:
            print("Operation completed successfully")
            sys.exit(0)
        else:
            print("Operation failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    