#!/bin/bash

# Azure Storage Container Management Script
# Equivalent to AWS S3 bucket operations

# Set strict mode for error handling
set -euo pipefail

# Function to show usage
usage() {
    echo "Usage: $0 <action> <container_name> <resource_group> <region>"
    echo "  action         - create, delete, or check"
    echo "  container_name - Name of the storage container"
    echo "  resource_group - Azure resource group name"
    echo "  region         - Azure region (e.g., eastus, westus, westeurope)"
    echo ""
    echo "Examples:"
    echo "  $0 create my-container myResourceGroup eastus"
    echo "  $0 delete my-container myResourceGroup eastus"
    echo "  $0 check my-container myResourceGroup eastus"
    exit 1
}

# Check if all required arguments are provided
if [ $# -ne 4 ]; then
    echo "Error: Missing required arguments"
    usage
fi

# Parse command line arguments
ACTION="$1"
CONTAINER_NAME="$2"
RESOURCE_GROUP="$3"
REGION="$4"

# Debug print arguments
echo "Action: $ACTION"
echo "Container: $CONTAINER_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo "Region: $REGION"
echo "------------------------"

# Function to check if storage account exists
storage_account_exists() {
    if az storage account show --name "$1" --resource-group "$2" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if container exists
container_exists() {
    local storage_account="$1"
    local container_name="$2"
    local resource_group="$3"
    
    # Get connection string
    local conn_str=$(az storage account show-connection-string \
        --name "$storage_account" \
        --resource-group "$resource_group" \
        --query connectionString \
        --output tsv 2>/dev/null || echo "")
    
    if [ -n "$conn_str" ]; then
        if az storage container exists \
            --name "$container_name" \
            --connection-string "$conn_str" \
            --query exists \
            --output tsv 2>/dev/null | grep -q "true"; then
            return 0
        fi
    fi
    return 1
}

# Function to create storage account if needed
create_storage_account() {
    local storage_account="$1"
    local resource_group="$2"
    local region="$3"
    
    if ! storage_account_exists "$storage_account" "$resource_group"; then
        echo "Creating storage account: $storage_account in $region..."
        
        if az storage account create \
            --name "$storage_account" \
            --resource-group "$resource_group" \
            --location "$region" \
            --sku Standard_LRS \
            --kind StorageV2; then
            echo "✅ Successfully created storage account: $storage_account"
        else
            echo "❌ Failed to create storage account: $storage_account"
            exit 1
        fi
    else
        echo "Storage account $storage_account already exists. Skipping creation."
    fi
}

# Function to create container
create_container() {
    local storage_account="$1"
    local container_name="$2"
    local resource_group="$3"
    
    # Create storage account first if it doesn't exist
    create_storage_account "$storage_account" "$resource_group" "$REGION"
    
    if container_exists "$storage_account" "$container_name" "$resource_group"; then
        echo "Container $container_name already exists. Skipping creation."
        return 0
    fi

    echo "Creating container $container_name in storage account $storage_account..."
    
    # Get connection string
    local conn_str=$(az storage account show-connection-string \
        --name "$storage_account" \
        --resource-group "$resource_group" \
        --query connectionString \
        --output tsv)
    
    if az storage container create \
        --name "$container_name" \
        --connection-string "$conn_str"; then
        echo "✅ Successfully created container: $container_name"
    else
        echo "❌ Failed to create container: $container_name"
        exit 1
    fi
}

# Function to delete container
delete_container() {
    local storage_account="$1"
    local container_name="$2"
    local resource_group="$3"
    
    if ! container_exists "$storage_account" "$container_name" "$resource_group"; then
        echo "Container $container_name does not exist. Skipping deletion."
        return 0
    fi

    echo "Deleting container $container_name..."
    
    # Get connection string
    local conn_str=$(az storage account show-connection-string \
        --name "$storage_account" \
        --resource-group "$resource_group" \
        --query connectionString \
        --output tsv)
    
    if az storage container delete \
        --name "$container_name" \
        --connection-string "$conn_str" \
        --yes; then
        echo "✅ Successfully deleted container: $container_name"
    else
        echo "❌ Failed to delete container: $container_name"
        exit 1
    fi
}

# Function to check container
check_container() {
    local storage_account="$1"
    local container_name="$2"
    local resource_group="$3"
    
    if container_exists "$storage_account" "$container_name" "$resource_group"; then
        echo "✅ Container $container_name exists"
        
        # Get container details
        local conn_str=$(az storage account show-connection-string \
            --name "$storage_account" \
            --resource-group "$resource_group" \
            --query connectionString \
            --output tsv)
        
        echo "Container details:"
        az storage container show \
            --name "$container_name" \
            --connection-string "$conn_str" \
            --query '{Name:name, LastModified:properties.lastModified}' \
            --output table 2>/dev/null || echo "   Could not retrieve details"
        
        exit 0
    else
        echo "❌ Container $container_name does not exist"
        exit 1
    fi
}

# Function to list containers
list_containers() {
    local storage_account="$1"
    local resource_group="$2"
    
    echo "Listing containers in storage account $storage_account:"
    
    # Get connection string
    local conn_str=$(az storage account show-connection-string \
        --name "$storage_account" \
        --resource-group "$resource_group" \
        --query connectionString \
        --output tsv)
    
    az storage container list \
        --connection-string "$conn_str" \
        --query '[].{Name:name, LastModified:properties.lastModified}' \
        --output table
}

# Function to list storage accounts
list_storage_accounts() {
    echo "Listing storage accounts in resource group $RESOURCE_GROUP:"
    az storage account list --resource-group "$RESOURCE_GROUP" --query '[].{Name:name, Location:location}' --output table
}

# Generate storage account name from container name (Azure requires unique names)
generate_storage_account_name() {
    local prefix=$(echo "$CONTAINER_NAME" | tr -cd 'a-z0-9' | cut -c1-15)
    local timestamp=$(date +%s | tail -c 4)
    echo "${prefix}${timestamp}"
}

# Main execution
STORAGE_ACCOUNT=$(generate_storage_account_name)

case "${ACTION}" in
    create)
        create_container "$STORAGE_ACCOUNT" "$CONTAINER_NAME" "$RESOURCE_GROUP"
        ;;
    delete)
        delete_container "$STORAGE_ACCOUNT" "$CONTAINER_NAME" "$RESOURCE_GROUP"
        ;;
    check)
        check_container "$STORAGE_ACCOUNT" "$CONTAINER_NAME" "$RESOURCE_GROUP"
        ;;
    list-containers)
        list_containers "$STORAGE_ACCOUNT" "$RESOURCE_GROUP"
        ;;
    list-accounts)
        list_storage_accounts
        ;;
    *)
        echo "Error: Invalid action '${ACTION}'"
        usage
        ;;
esac

echo "Operation completed successfully"
