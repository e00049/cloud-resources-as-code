#!/usr/bin/env python3
"""
GCS Bucket Management using Python Client Library
Usage: python3 script.py <action> <bucket_name> <location> <project_id>
"""

import sys
from google.cloud import storage
from google.api_core.exceptions import Conflict, NotFound


def create_bucket(bucket_name, location, project_id, storage_class="STANDARD"):
    """Create a new GCS bucket."""
    try:
        storage_client = storage.Client(project=project_id)
        
        # Check if bucket already exists
        try:
            storage_client.get_bucket(bucket_name)
            print(f"Bucket {bucket_name} already exists. Skipping creation.")
            return True
        except NotFound:
            pass  # Bucket doesn't exist, proceed with creation
        
        # Create the bucket
        bucket = storage_client.bucket(bucket_name)
        bucket.location = location
        bucket.storage_class = storage_class
        
        bucket = storage_client.create_bucket(bucket)
        print(f"✅ Bucket {bucket.name} created successfully in {location}")
        return True
        
    except Conflict:
        print(f"❌ Bucket {bucket_name} already exists (Conflict error).")
        return False
    except Exception as e:
        print(f"❌ Failed to create bucket {bucket_name}: {e}")
        return False

def delete_bucket(bucket_name, project_id):
    """Delete a GCS bucket."""
    try:
        storage_client = storage.Client(project=project_id)
        
        # Get the bucket
        try:
            bucket = storage_client.get_bucket(bucket_name)
        except NotFound:
            print(f"Bucket {bucket_name} does not exist. Skipping deletion.")
            return True
        
        # Try to delete all objects first (optional but good practice)
        print(f"Attempting to delete all objects in bucket {bucket_name}...")
        try:
            blobs = list(bucket.list_blobs())
            if blobs:
                bucket.delete_blobs(blobs)
                print(f"Deleted {len(blobs)} objects from bucket.")
        except Exception as e:
            print(f"Warning: Could not delete objects: {e}")
        
        # Delete the bucket
        bucket.delete()
        print(f"✅ Bucket {bucket_name} deleted successfully.")
        return True
        
    except NotFound:
        print(f"Bucket {bucket_name} does not exist.")
        return True
    except Exception as e:
        print(f"❌ Failed to delete bucket {bucket_name}: {e}")
        return False

def check_bucket(bucket_name, project_id):
    """Check if a bucket exists."""
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.get_bucket(bucket_name)
        print(f"✅ Bucket {bucket_name} exists")
        print(f"   Location: {bucket.location}")
        print(f"   Storage Class: {bucket.storage_class}")
        print(f"   Created: {bucket.time_created}")
        return True
    except NotFound:
        print(f"❌ Bucket {bucket_name} does not exist")
        return False
    except Exception as e:
        print(f"❌ Error checking bucket {bucket_name}: {e}")
        return False

def main():
    """Main function to parse arguments and execute the appropriate action."""
    if len(sys.argv) != 5:
        print("Usage: python3 script.py <action> <bucket_name> <location> <project_id>")
        print("Actions: create, delete, check")
        sys.exit(1)
    
    action = sys.argv[1]
    bucket_name = sys.argv[2]
    location = sys.argv[3]
    project_id = sys.argv[4]
    
    print(f"Action: {action}")
    print(f"Bucket: {bucket_name}")
    print(f"Location: {location}")
    print(f"Project: {project_id}")
    print("-" * 40)
    
    success = False
    if action == "create":
        success = create_bucket(bucket_name, location, project_id)
    elif action == "delete":
        success = delete_bucket(bucket_name, project_id)
    elif action == "check":
        success = check_bucket(bucket_name, project_id)
    else:
        print(f"Invalid action: {action}. Use create, delete, or check.")
        sys.exit(1)
    
    if success:
        print("Operation completed successfully")
        sys.exit(0)
    else:
        print("Operation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
