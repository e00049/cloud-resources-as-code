package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"cloud.google.com/go/storage"
)

func main() {
	// Check command line arguments
	if len(os.Args) != 5 {
		fmt.Println("Usage: go run 04-golang-bucket.go <action> <bucketName> <location> <projectId>")
		fmt.Println("Actions: create, delete, check")
		os.Exit(1)
	}

	action := os.Args[1]
	bucketName := os.Args[2]
	location := os.Args[3]
	projectId := os.Args[4]

	fmt.Printf("Action: %s\n", action)
	fmt.Printf("Bucket: %s\n", bucketName)
	fmt.Printf("Location: %s\n", location)
	fmt.Printf("Project: %s\n", projectId)
	fmt.Println("------------------------")

	// Create Google Cloud Storage client
	ctx := context.Background()
	client, err := storage.NewClient(ctx)
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	switch action {
	case "create":
		createBucket(ctx, client, bucketName, location, projectId)
	case "delete":
		deleteBucket(ctx, client, bucketName)
	case "check":
		checkBucket(ctx, client, bucketName)
	default:
		fmt.Printf("Invalid action: %s. Use create, delete, or check.\n", action)
		os.Exit(1)
	}
}

func createBucket(ctx context.Context, client *storage.Client, bucketName, location, projectId string) {
	// Check if bucket already exists
	bucket := client.Bucket(bucketName)
	_, err := bucket.Attrs(ctx)
	if err == nil {
		fmt.Printf("Bucket %s already exists.\n", bucketName)
		return
	}

	// Create the bucket
	err = bucket.Create(ctx, projectId, &storage.BucketAttrs{
		Location: location,
	})
	if err != nil {
		log.Fatalf("Failed to create bucket: %v", err)
	}

	fmt.Printf("✅ Bucket %s created successfully in %s\n", bucketName, location)
}

func deleteBucket(ctx context.Context, client *storage.Client, bucketName string) {
	bucket := client.Bucket(bucketName)
	
	// Check if bucket exists
	_, err := bucket.Attrs(ctx)
	if err != nil {
		fmt.Printf("Bucket %s does not exist.\n", bucketName)
		return
	}

	// Delete the bucket
	err = bucket.Delete(ctx)
	if err != nil {
		log.Fatalf("Failed to delete bucket: %v", err)
	}

	fmt.Printf("✅ Bucket %s deleted successfully.\n", bucketName)
}

func checkBucket(ctx context.Context, client *storage.Client, bucketName string) {
	bucket := client.Bucket(bucketName)
	attrs, err := bucket.Attrs(ctx)
	
	if err != nil {
		fmt.Printf("❌ Bucket %s does not exist.\n", bucketName)
		return
	}

	fmt.Printf("✅ Bucket %s exists\n", bucketName)
	fmt.Printf("   Location: %s\n", attrs.Location)
	fmt.Printf("   Storage Class: %s\n", attrs.StorageClass)
	fmt.Printf("   Created: %s\n", attrs.Created)
}
