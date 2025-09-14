#!/usr/bin/env node
/**
 * GCS Bucket Management using Node.js Client Library
 * Usage: node script.js <action> <bucket_name> <location> <project_id>
 */

const { Storage } = require('@google-cloud/storage');
const process = require('process');

async function createBucket(bucketName, location, projectId, storageClass = 'STANDARD') {
    try {
        const storage = new Storage({ projectId });
        
        // Check if bucket already exists
        const [buckets] = await storage.getBuckets();
        const bucketExists = buckets.some(bucket => bucket.name === bucketName);
        
        if (bucketExists) {
            console.log(`Bucket ${bucketName} already exists. Skipping creation.`);
            return true;
        }
        
        // Create the bucket
        const [bucket] = await storage.createBucket(bucketName, {
            location: location,
            storageClass: storageClass
        });
        
        console.log(`✅ Bucket ${bucket.name} created successfully in ${location}`);
        return true;
        
    } catch (error) {
        if (error.code === 409) { // Bucket already exists
            console.log(`Bucket ${bucketName} already exists.`);
            return true;
        }
        console.error(`❌ Failed to create bucket ${bucketName}:`, error.message);
        return false;
    }
}

async function deleteBucket(bucketName, projectId) {
    try {
        const storage = new Storage({ projectId });
        
        // Get the bucket
        const bucket = storage.bucket(bucketName);
        
        // Check if bucket exists
        const [exists] = await bucket.exists();
        if (!exists) {
            console.log(`Bucket ${bucketName} does not exist. Skipping deletion.`);
            return true;
        }
        
        // Try to delete all objects first
        console.log(`Attempting to delete all objects in bucket ${bucketName}...`);
        try {
            const [files] = await bucket.getFiles();
            if (files.length > 0) {
                await Promise.all(files.map(file => file.delete()));
                console.log(`Deleted ${files.length} objects from bucket.`);
            }
        } catch (error) {
            console.log(`Warning: Could not delete objects: ${error.message}`);
        }
        
        // Delete the bucket
        await bucket.delete();
        console.log(`✅ Bucket ${bucketName} deleted successfully.`);
        return true;
        
    } catch (error) {
        if (error.code === 404) { // Bucket not found
            console.log(`Bucket ${bucketName} does not exist.`);
            return true;
        }
        console.error(`❌ Failed to delete bucket ${bucketName}:`, error.message);
        return false;
    }
}

async function checkBucket(bucketName, projectId) {
    try {
        const storage = new Storage({ projectId });
        const bucket = storage.bucket(bucketName);
        
        // Check if bucket exists and get metadata
        const [exists] = await bucket.exists();
        if (exists) {
            const [metadata] = await bucket.getMetadata();
            console.log(`✅ Bucket ${bucketName} exists`);
            console.log(`   Location: ${metadata.location}`);
            console.log(`   Storage Class: ${metadata.storageClass}`);
            console.log(`   Created: ${metadata.timeCreated}`);
            return true;
        } else {
            console.log(`❌ Bucket ${bucketName} does not exist`);
            return false;
        }
        
    } catch (error) {
        console.error(`❌ Error checking bucket ${bucketName}:`, error.message);
        return false;
    }
}

async function main() {
    // Parse command line arguments
    const args = process.argv.slice(2);
    
    if (args.length !== 4) {
        console.log('Usage: node script.js <action> <bucket_name> <location> <project_id>');
        console.log('Actions: create, delete, check');
        process.exit(1);
    }
    
    const [action, bucketName, location, projectId] = args;
    
    console.log(`Action: ${action}`);
    console.log(`Bucket: ${bucketName}`);
    console.log(`Location: ${location}`);
    console.log(`Project: ${projectId}`);
    console.log('─'.repeat(40));
    
    let success = false;
    
    try {
        switch (action) {
            case 'create':
                success = await createBucket(bucketName, location, projectId);
                break;
            case 'delete':
                success = await deleteBucket(bucketName, projectId);
                break;
            case 'check':
                success = await checkBucket(bucketName, projectId);
                break;
            default:
                console.log(`Invalid action: ${action}. Use create, delete, or check.`);
                process.exit(1);
        }
        
        if (success) {
            console.log('Operation completed successfully');
            process.exit(0);
        } else {
            console.log('Operation failed');
            process.exit(1);
        }
        
    } catch (error) {
        console.error('Unexpected error:', error.message);
        process.exit(1);
    }
}

// Run the main function
main().catch(console.error);
