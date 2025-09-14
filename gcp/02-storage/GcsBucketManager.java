import com.google.cloud.storage.Blob;
import com.google.cloud.storage.Bucket;
import com.google.cloud.storage.BucketInfo;
import com.google.cloud.storage.Storage;
import com.google.cloud.storage.StorageClass;
import com.google.cloud.storage.StorageException;
import com.google.cloud.storage.StorageOptions;
package com.example.gcs;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

public class GcsBucketManager {

    private final Storage storage;

    public GcsBucketManager(String projectId) {
        this.storage = StorageOptions.newBuilder().setProjectId(projectId).build().getService();
    }

    /**
     * Creates a new GCS bucket.
     */
    public boolean createBucket(String bucketName, String location) {
        try {
            Bucket bucket = storage.get(bucketName);
            if (bucket != null) {
                System.out.printf("Bucket %s already exists. Skipping creation.%n", bucketName);
                return true;
            }

            BucketInfo bucketInfo = BucketInfo.newBuilder(bucketName)
                    .setLocation(location)
                    .setStorageClass(StorageClass.STANDARD)
                    .build();
            storage.create(bucketInfo);
            System.out.printf("✅ Bucket %s created successfully in %s%n", bucketName, location);
            return true;
        } catch (StorageException e) {
            System.out.printf("❌ Failed to create bucket %s: %s%n", bucketName, e.getMessage());
            return false;
        }
    }

    /**
     * Deletes a GCS bucket and all its contents.
     */
    public boolean deleteBucket(String bucketName) {
        try {
            Bucket bucket = storage.get(bucketName);
            if (bucket == null) {
                System.out.printf("Bucket %s does not exist. Skipping deletion.%n", bucketName);
                return true;
            }

            System.out.printf("Attempting to delete all objects in bucket %s...%n", bucketName);
            try {
                List<Blob> blobs = new ArrayList<>();
                storage.list(bucketName).iterateAll().forEach(blobs::add);
                if (!blobs.isEmpty()) {
                    List<String> blobNames = blobs.stream().map(Blob::getName).collect(Collectors.toList());
                    storage.delete(bucketName, blobNames);
                    System.out.printf("Deleted %d objects from bucket.%n", blobNames.size());
                }
            } catch (StorageException e) {
                System.err.printf("Warning: Could not delete objects: %s%n", e.getMessage());
            }

            storage.delete(bucketName);
            System.out.printf("✅ Bucket %s deleted successfully.%n", bucketName);
            return true;
        } catch (StorageException e) {
            System.out.printf("❌ Failed to delete bucket %s: %s%n", bucketName, e.getMessage());
            return false;
        }
    }

    /**
     * Checks if a bucket exists and prints its details.
     */
    public boolean checkBucket(String bucketName) {
        try {
            Bucket bucket = storage.get(bucketName, Storage.BucketGetOption.fields(Storage.BucketField.values()));
            if (bucket != null) {
                System.out.printf("✅ Bucket %s exists%n", bucketName);
                System.out.printf("   Location: %s%n", bucket.getLocation());
                System.out.printf("   Storage Class: %s%n", bucket.getStorageClass());
                System.out.printf("   Created: %s%n", bucket.getCreateTimeOffsetDateTime());
                return true;
            } else {
                System.out.printf("❌ Bucket %s does not exist%n", bucketName);
                return false;
            }
        } catch (StorageException e) {
            System.out.printf("❌ Error checking bucket %s: %s%n", bucketName, e.getMessage());
            return false;
        }
    }

    public static void main(String[] args) {
        if (args.length != 4) {
            System.out.println("Usage: java GcsBucketManager <action> <bucket_name> <location> <project_id>");
            System.out.println("Actions: create, delete, check");
            System.exit(1);
        }

        String action = args[0];
        String bucketName = args[1];
        String location = args[2];
        String projectId = args[3];

        System.out.printf("Action: %s%n", action);
        System.out.printf("Bucket: %s%n", bucketName);
        System.out.printf("Location: %s%n", location);
        System.out.printf("Project: %s%n", projectId);
        System.out.println("----------------------------------------");

        GcsBucketManager manager = new GcsBucketManager(projectId);
        boolean success = false;

        switch (action) {
            case "create":
                success = manager.createBucket(bucketName, location);
                break;
            case "delete":
                success = manager.deleteBucket(bucketName);
                break;
            case "check":
                success = manager.checkBucket(bucketName);
                break;
            default:
                System.out.printf("Invalid action: %s. Use create, delete, or check.%n", action);
                System.exit(1);
        }

        if (success) {
            System.out.println("Operation completed successfully");
            System.exit(0);
        } else {
            System.out.println("Operation failed");
            System.exit(1);
        }
    }
}
