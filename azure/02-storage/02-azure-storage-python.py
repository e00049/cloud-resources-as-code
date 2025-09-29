#!/usr/bin/env python3
"""
Azure Storage Container Management Script
Equivalent to AWS S3 bucket operations
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AzureStorageManager:
    def __init__(self, resource_group: str, region: str):
        """Initialize Azure Storage Manager with credentials"""
        try:
            self.credential = DefaultAzureCredential()
            self.storage_client = StorageManagementClient(self.credential, subscription_id=self._get_subscription_id())
            self.resource_group = resource_group
            self.region = region
        except Exception as e:
            logger.error(f"Failed to initialize Azure clients: {e}")
            sys.exit(1)

    def _get_subscription_id(self) -> str:
        """Get Azure subscription ID from environment or user input"""
        subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
        if not subscription_id:
            logger.error("AZURE_SUBSCRIPTION_ID environment variable not set")
            sys.exit(1)
        return subscription_id

    def generate_storage_account_name(self, container_name: str) -> str:
        """Generate unique storage account name from container name"""
        import hashlib
        import time
        
        # Azure storage account names must be 3-24 chars, lowercase alphanumeric
        prefix = container_name.lower().replace('-', '')[:15]
        timestamp = str(int(time.time()))[-4:]
        hash_suffix = hashlib.md5(container_name.encode()).hexdigest()[:4]
        
        return f"{prefix}{timestamp}{hash_suffix}"[:24]

    def storage_account_exists(self, storage_account: str) -> bool:
        """Check if storage account exists"""
        try:
            self.storage_client.storage_accounts.get_properties(
                self.resource_group, storage_account
            )
            return True
        except ResourceNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking storage account existence: {e}")
            return False

    def container_exists(self, storage_account: str, container_name: str) -> bool:
        """Check if container exists in storage account"""
        try:
            blob_service_client = self._get_blob_service_client(storage_account)
            container_client = blob_service_client.get_container_client(container_name)
            return container_client.exists()
        except Exception as e:
            logger.error(f"Error checking container existence: {e}")
            return False

    def _get_blob_service_client(self, storage_account: str) -> BlobServiceClient:
        """Get BlobServiceClient for a storage account"""
        try:
            # Get storage account keys
            keys = self.storage_client.storage_accounts.list_keys(
                self.resource_group, storage_account
            )
            connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={storage_account};"
                f"AccountKey={keys.keys[0].value};"
                f"EndpointSuffix=core.windows.net"
            )
            return BlobServiceClient.from_connection_string(connection_string)
        except Exception as e:
            logger.error(f"Failed to get blob service client: {e}")
            raise

    def create_storage_account(self, storage_account: str) -> bool:
        """Create storage account if it doesn't exist"""
        if self.storage_account_exists(storage_account):
            logger.info(f"Storage account {storage_account} already exists. Skipping creation.")
            return True

        logger.info(f"Creating storage account: {storage_account} in {self.region}...")
        
        try:
            async_poller = self.storage_client.storage_accounts.begin_create(
                self.resource_group,
                storage_account,
                {
                    "location": self.region,
                    "kind": "StorageV2",
                    "sku": {"name": "Standard_LRS"},
                    "properties": {
                        "access_tier": "Hot",
                        "minimum_tls_version": "TLS1_2"
                    }
                }
            )
            # Wait for completion
            async_poller.result()
            logger.info(f"✅ Successfully created storage account: {storage_account}")
            return True
        except ResourceExistsError:
            logger.info(f"Storage account {storage_account} was created by another process")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create storage account: {e}")
            return False

    def create_container(self, storage_account: str, container_name: str) -> bool:
        """Create container in storage account"""
        # Create storage account first if needed
        if not self.create_storage_account(storage_account):
            return False

        if self.container_exists(storage_account, container_name):
            logger.info(f"Container {container_name} already exists. Skipping creation.")
            return True

        logger.info(f"Creating container {container_name} in storage account {storage_account}...")
        
        try:
            blob_service_client = self._get_blob_service_client(storage_account)
            container_client = blob_service_client.create_container(container_name)
            logger.info(f"✅ Successfully created container: {container_name}")
            return True
        except ResourceExistsError:
            logger.info(f"Container {container_name} was created by another process")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create container: {e}")
            return False

    def delete_container(self, storage_account: str, container_name: str) -> bool:
        """Delete container from storage account"""
        if not self.container_exists(storage_account, container_name):
            logger.info(f"Container {container_name} does not exist. Skipping deletion.")
            return True

        logger.info(f"Deleting container {container_name}...")
        
        try:
            blob_service_client = self._get_blob_service_client(storage_account)
            container_client = blob_service_client.get_container_client(container_name)
            container_client.delete_container()
            logger.info(f"✅ Successfully deleted container: {container_name}")
            return True
        except ResourceNotFoundError:
            logger.info(f"Container {container_name} was already deleted")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete container: {e}")
            return False

    def check_container(self, storage_account: str, container_name: str) -> bool:
        """Check if container exists and show details"""
        if not self.container_exists(storage_account, container_name):
            logger.error(f"❌ Container {container_name} does not exist")
            return False

        logger.info(f"✅ Container {container_name} exists")
        
        try:
            blob_service_client = self._get_blob_service_client(storage_account)
            container_client = blob_service_client.get_container_client(container_name)
            properties = container_client.get_container_properties()
            
            print(f"\nContainer Details:")
            print(f"  Name: {properties.name}")
            print(f"  Last Modified: {properties.last_modified}")
            print(f"  ETag: {properties.etag}")
            print(f"  Lease Status: {properties.lease.status if properties.lease else 'None'}")
            
            return True
        except Exception as e:
            logger.error(f"Could not retrieve container details: {e}")
            return False

    def list_containers(self, storage_account: str):
        """List all containers in storage account"""
        if not self.storage_account_exists(storage_account):
            logger.error(f"Storage account {storage_account} does not exist")
            return

        logger.info(f"Listing containers in storage account {storage_account}:")
        
        try:
            blob_service_client = self._get_blob_service_client(storage_account)
            containers = blob_service_client.list_containers()
            
            print(f"\n{'Container Name':<30} {'Last Modified':<25}")
            print("-" * 55)
            for container in containers:
                last_modified = container.last_modified.strftime("%Y-%m-%d %H:%M:%S") if container.last_modified else "N/A"
                print(f"{container.name:<30} {last_modified:<25}")
                
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")

    def list_storage_accounts(self):
        """List all storage accounts in resource group"""
        logger.info(f"Listing storage accounts in resource group {self.resource_group}:")
        
        try:
            accounts = self.storage_client.storage_accounts.list_by_resource_group(self.resource_group)
            
            print(f"\n{'Account Name':<25} {'Location':<20} {'SKU':<15} {'Status':<10}")
            print("-" * 70)
            for account in accounts:
                status = account.status_of_primary if account.status_of_primary else "N/A"
                sku = account.sku.name if account.sku else "N/A"
                print(f"{account.name:<25} {account.location:<20} {sku:<15} {status:<10}")
                
        except Exception as e:
            logger.error(f"Failed to list storage accounts: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Azure Storage Container Management Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create my-container myResourceGroup eastus
  %(prog)s delete my-container myResourceGroup eastus
  %(prog)s check my-container myResourceGroup eastus
  %(prog)s list-containers my-container myResourceGroup eastus
  %(prog)s list-accounts myResourceGroup eastus
        """
    )
    
    parser.add_argument("action", 
                       choices=["create", "delete", "check", "list-containers", "list-accounts"],
                       help="Action to perform")
    parser.add_argument("container_name", nargs="?", 
                       help="Name of the storage container")
    parser.add_argument("resource_group", 
                       help="Azure resource group name")
    parser.add_argument("region", nargs="?", 
                       help="Azure region (e.g., eastus, westus, westeurope)")
    
    args = parser.parse_args()
    
    # Validate arguments based on action
    if args.action in ["create", "delete", "check", "list-containers"] and not args.container_name:
        parser.error(f"container_name is required for action '{args.action}'")
    
    if args.action in ["create", "delete", "check", "list-containers"] and not args.region:
        parser.error(f"region is required for action '{args.action}'")
    
    if args.action == "list-accounts" and not args.region:
        parser.error(f"region is required for action '{args.action}'")
    
    # Debug print arguments
    print(f"Action: {args.action}")
    if args.container_name:
        print(f"Container: {args.container_name}")
    print(f"Resource Group: {args.resource_group}")
    if args.region:
        print(f"Region: {args.region}")
    print("------------------------")
    
    try:
        # Initialize Azure Storage Manager
        manager = AzureStorageManager(args.resource_group, args.region)
        
        if args.action == "list-accounts":
            manager.list_storage_accounts()
            return
        
        # Generate storage account name
        storage_account = manager.generate_storage_account_name(args.container_name)
        
        # Execute action
        if args.action == "create":
            success = manager.create_container(storage_account, args.container_name)
        elif args.action == "delete":
            success = manager.delete_container(storage_account, args.container_name)
        elif args.action == "check":
            success = manager.check_container(storage_account, args.container_name)
        elif args.action == "list-containers":
            manager.list_containers(storage_account)
            success = True
        else:
            logger.error(f"Invalid action: {args.action}")
            sys.exit(1)
        
        if success:
            print("Operation completed successfully")
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if required environment variable is set
    if not os.environ.get('AZURE_SUBSCRIPTION_ID'):
        print("Error: AZURE_SUBSCRIPTION_ID environment variable must be set")
        print("Export your Azure subscription ID:")
        print("  export AZURE_SUBSCRIPTION_ID='your-subscription-id'")
        sys.exit(1)
    
    main()
