provider "aws" {
  region = "ap-south-1"  # Default region
  
  # Authentication is automatic - uses same credentials as AWS CLI
  # Reads from:
  # - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables
  # - ~/.aws/credentials file
  # - IAM instance profile (if running on EC2)
}

# Create an S3 bucket
resource "aws_s3_bucket" "my_bucket" {
  bucket = "e00049-terraform-bucket"  # Must be globally unique
  
  # Optional: Add tags for better management
  tags = {
    Name        = "My Terraform Bucket"
    Environment = "Development"
    CreatedBy   = "Terraform"
  }
}
