#!/usr/bin/env node
/**
 * AWS S3 Bucket Management using Node.js AWS SDK
 * Usage: node script.js <action> <bucket_name> <region>
 */

const { S3Client, CreateBucketCommand, DeleteBucketCommand, HeadBucketCommand, ListBucketsCommand } = require('@aws-sdk/client-s3');
const { fromIni } = require('@aws-sdk/credential-providers');

function usage() {
    console.log("Usage: node script.js <action> <bucket_name> <region>");
    console.log("  action      - create, delete, check, or list");
    console.log("  bucket_name - Name of the S3 bucket (e.g., my-bucket)");
    console.log("  region      - AWS region (e.g., ap-south-1, us-east-1)");
    console.log("");
    console.log("Examples:");
    console.log("  node script.js create my-bucket ap-south-1");
    console.log("  node script.js delete my-bucket ap-south-1");
    console.log("  node script.js check my-bucket ap-south-1");
    console.log("  node script.js list");
    process.exit(1);
}

function createS3Client(region) {
    try {
        return new S3Client({
            region: region,
            credentials: fromIni({ profile: 'default' })
        });
    } catch (error) {
        console.error('❌ Failed to create S3 client:', error.message);
        process.exit(1);
    }
}

async function bucketExists(s3Client, bucketName) {
    try {
        await s3Client.send(new HeadBucketCommand({ Bucket: bucketName }));
        return true;
    } catch (error) {
        if (error.name === 'NotFound') {
            return false;
        } else if (error.name === 'Forbidden') {
            console.log('❌ Access denied to bucket. Check permissions.');
            process.exit(1);
        }
        return false;
    }
}

async function createBucket(s3Client, bucketName, region) {
    if (await bucketExists(s3Client, bucketName)) {
        console.log(`Bucket s3://${bucketName} already exists. Skipping creation.`);
        return true;
    }

    console.log(`Creating bucket s3://${bucketName} in ${region}...`);

    try {
        const command = new CreateBucketCommand({ 
            Bucket: bucketName,
            ...(region !== 'us-east-1' && {
                CreateBucketConfiguration: {
                    LocationConstraint: region
                }
            })
        });
        
        await s3Client.send(command);
        console.log(`✅ Successfully created bucket: s3://${bucketName}`);
        return true;
    } catch (error) {
        if (error.name === 'BucketAlreadyExists') {
            console.log(`Bucket s3://${bucketName} already exists.`);
            return true;
        } else if (error.name === 'BucketAlreadyOwnedByYou') {
            console.log(`Bucket s3://${bucketName} already owned by you.`);
            return true;
        } else {
            console.log(`❌ Failed to create bucket: ${error.message}`);
            return false;
        }
    }
}

async function deleteBucket(s3Client, bucketName, region) {
    if (!await bucketExists(s3Client, bucketName)) {
        console.log(`Bucket s3://${bucketName} does not exist. Skipping deletion.`);
        return true;
    }

    console.log(`Deleting bucket s3://${bucketName}...`);

    try {
        // Note: In real applications, you should empty the bucket first
        // This requires additional operations to delete all objects
        const command = new DeleteBucketCommand({ Bucket: bucketName });
        await s3Client.send(command);
        console.log(`✅ Successfully deleted bucket: s3://${bucketName}`);
        return true;
    } catch (error) {
        console.log(`❌ Failed to delete bucket: ${error.message}`);
        return false;
    }
}

async function checkBucket(s3Client, bucketName) {
    if (await bucketExists(s3Client, bucketName)) {
        console.log(`✅ Bucket s3://${bucketName} exists`);
        
        try {
            // Get bucket location
            const location = await s3Client.send(new HeadBucketCommand({ Bucket: bucketName }));
            console.log(`   Region: ${location.$metadata.httpStatusCode === 200 ? 'Available' : 'Unknown'}`);
            
            // For more details, we'd need to list all buckets and find creation date
            const listCommand = new ListBucketsCommand({});
            const buckets = await s3Client.send(listCommand);
            const bucketInfo = buckets.Buckets.find(b => b.Name === bucketName);
            
            if (bucketInfo) {
                console.log(`   Created: ${bucketInfo.CreationDate}`);
            }
        } catch (error) {
            console.log(`   Could not retrieve details: ${error.message}`);
        }
        
        return true;
    } else {
        console.log(`❌ Bucket s3://${bucketName} does not exist`);
        return false;
    }
}

async function listBuckets(s3Client) {
    console.log("Listing all S3 buckets:");
    try {
        const command = new ListBucketsCommand({});
        const response = await s3Client.send(command);
        
        if (!response.Buckets || response.Buckets.length === 0) {
            console.log("   No buckets found");
        } else {
            response.Buckets.forEach(bucket => {
                console.log(`   ${bucket.Name} - Created: ${bucket.CreationDate}`);
            });
        }
        return true;
    } catch (error) {
        console.log(`❌ Failed to list buckets: ${error.message}`);
        return false;
    }
}

async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        usage();
    }

    const action = args[0];

    // Handle list action
    if (action === 'list' && args.length === 1) {
        const s3Client = createS3Client('us-east-1');
        const success = await listBuckets(s3Client);
        process.exit(success ? 0 : 1);
    }

    // Handle other actions
    if (args.length !== 3) {
        usage();
    }

    const bucketName = args[1];
    const region = args[2];

    console.log(`Action: ${action}`);
    console.log(`Bucket: s3://${bucketName}`);
    console.log(`Region: ${region}`);
    console.log("------------------------");

    const s3Client = createS3Client(region);
    let success = false;

    try {
        switch (action) {
            case 'create':
                success = await createBucket(s3Client, bucketName, region);
                break;
            case 'delete':
                success = await deleteBucket(s3Client, bucketName, region);
                break;
            case 'check':
                success = await checkBucket(s3Client, bucketName);
                break;
            default:
                console.log(`Error: Invalid action '${action}'`);
                usage();
        }

        if (success) {
            console.log("Operation completed successfully");
            process.exit(0);
        } else {
            console.log("Operation failed");
            process.exit(1);
        }
    } catch (error) {
        console.log(`❌ Unexpected error: ${error.message}`);
        process.exit(1);
    }
}

// Run the main function
main().catch(console.error);
