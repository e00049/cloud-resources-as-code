package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
)

func usage() {
	fmt.Println("Usage: go run script.go <action> <bucket_name> <region>")
	fmt.Println("  action      - create, delete, check, or list")
	fmt.Println("  bucket_name - Name of the S3 bucket (e.g., my-bucket)")
	fmt.Println("  region      - AWS region (e.g., ap-south-1, us-east-1)")
	fmt.Println("")
	fmt.Println("Examples:")
	fmt.Println("  go run script.go create my-bucket ap-south-1")
	fmt.Println("  go run script.go delete my-bucket ap-south-1")
	fmt.Println("  go run script.go check my-bucket ap-south-1")
	fmt.Println("  go run script.go list")
	os.Exit(1)
}

func createS3Client(region string) *s3.Client {
	// Load AWS configuration automatically from:
	// - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
	// - ~/.aws/credentials file
	// - IAM roles (if running on EC2)
	cfg, err := config.LoadDefaultConfig(context.TODO(),
		config.WithRegion(region),
	)
	if err != nil {
		log.Fatalf("❌ Failed to load AWS configuration: %v", err)
	}

	return s3.NewFromConfig(cfg)
}

func bucketExists(s3Client *s3.Client, bucketName string) bool {
	_, err := s3Client.HeadBucket(context.TODO(), &s3.HeadBucketInput{
		Bucket: aws.String(bucketName),
	})
	
	if err != nil {
		// Check if it's a "not found" error
		return false
	}
	return true
}

func createBucket(s3Client *s3.Client, bucketName, region string) {
	if bucketExists(s3Client, bucketName) {
		fmt.Printf("Bucket s3://%s already exists. Skipping creation.\n", bucketName)
		return
	}

	fmt.Printf("Creating bucket s3://%s in %s...\n", bucketName, region)

	// Create bucket input
	input := &s3.CreateBucketInput{
		Bucket: aws.String(bucketName),
	}

	// For regions other than us-east-1, specify LocationConstraint
	if region != "us-east-1" {
		input.CreateBucketConfiguration = &types.CreateBucketConfiguration{
			LocationConstraint: types.BucketLocationConstraint(region),
		}
	}

	_, err := s3Client.CreateBucket(context.TODO(), input)
	if err != nil {
		log.Fatalf("❌ Failed to create bucket: %v", err)
	}

	fmt.Printf("✅ Successfully created bucket: s3://%s\n", bucketName)
}

func deleteBucket(s3Client *s3.Client, bucketName string) {
	if !bucketExists(s3Client, bucketName) {
		fmt.Printf("Bucket s3://%s does not exist. Skipping deletion.\n", bucketName)
		return
	}

	fmt.Printf("Deleting bucket s3://%s...\n", bucketName)

	// Note: In production, you should empty the bucket first
	// This requires additional operations to delete all objects

	_, err := s3Client.DeleteBucket(context.TODO(), &s3.DeleteBucketInput{
		Bucket: aws.String(bucketName),
	})
	if err != nil {
		log.Fatalf("❌ Failed to delete bucket: %v", err)
	}

	fmt.Printf("✅ Successfully deleted bucket: s3://%s\n", bucketName)
}

func checkBucket(s3Client *s3.Client, bucketName string) {
	if bucketExists(s3Client, bucketName) {
		fmt.Printf("✅ Bucket s3://%s exists\n", bucketName)
		
		// Try to get more details
		locationOutput, err := s3Client.GetBucketLocation(context.TODO(), &s3.GetBucketLocationInput{
			Bucket: aws.String(bucketName),
		})
		if err == nil {
			fmt.Printf("   Region: %s\n", string(locationOutput.LocationConstraint))
		}

		// Try to get creation date by listing all buckets
		listOutput, err := s3Client.ListBuckets(context.TODO(), &s3.ListBucketsInput{})
		if err == nil {
			for _, bucket := range listOutput.Buckets {
				if *bucket.Name == bucketName {
					fmt.Printf("   Created: %s\n", bucket.CreationDate.Format(time.RFC3339))
					break
				}
			}
		}
	} else {
		fmt.Printf("❌ Bucket s3://%s does not exist\n", bucketName)
		os.Exit(1)
	}
}

func listBuckets(s3Client *s3.Client) {
	fmt.Println("Listing all S3 buckets:")
	
	output, err := s3Client.ListBuckets(context.TODO(), &s3.ListBucketsInput{})
	if err != nil {
		log.Fatalf("❌ Failed to list buckets: %v", err)
	}

	if len(output.Buckets) == 0 {
		fmt.Println("   No buckets found")
		return
	}

	for _, bucket := range output.Buckets {
		fmt.Printf("   %s - Created: %s\n", *bucket.Name, bucket.CreationDate.Format("2006-01-02"))
	}
}

func main() {
	if len(os.Args) < 2 {
		usage()
	}

	action := os.Args[1]

	// Handle list action
	if action == "list" && len(os.Args) == 2 {
		s3Client := createS3Client("us-east-1") // Default region for listing
		listBuckets(s3Client)
		os.Exit(0)
	}

	// Handle other actions
	if len(os.Args) != 4 {
		usage()
	}

	bucketName := os.Args[2]
	region := os.Args[3]

	fmt.Printf("Action: %s\n", action)
	fmt.Printf("Bucket: s3://%s\n", bucketName)
	fmt.Printf("Region: %s\n", region)
	fmt.Println("------------------------")

	s3Client := createS3Client(region)

	switch action {
	case "create":
		createBucket(s3Client, bucketName, region)
	case "delete":
		deleteBucket(s3Client, bucketName)
	case "check":
		checkBucket(s3Client, bucketName)
	default:
		fmt.Printf("Error: Invalid action '%s'\n", action)
		usage()
	}

	fmt.Println("Operation completed successfully")
}
