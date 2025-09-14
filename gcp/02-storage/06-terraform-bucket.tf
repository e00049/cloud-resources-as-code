# Configure the Google Cloud provider
provider "google" {
  project = "e00049-development-project"  # Your project ID
  region  = "asia-south1"                 # Default region
}

# Create a Google Cloud Storage bucket
resource "google_storage_bucket" "my_bucket" {
  name          = "e00049-terraform-bucket"  # Unique bucket name
  location      = "asia-south1"              # Bucket location
  storage_class = "STANDARD"                 # Storage class

  # Optional: Enable versioning
  versioning {
    enabled = true
  }

  # Optional: Add labels
  labels = {
    created-by  = "terraform"
    environment = "development"
  }

  # Optional: Lifecycle rules
  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  # Delete objects after 30 days
    }
  }
}

# Output the bucket URL
output "bucket_url" {
  value = google_storage_bucket.my_bucket.url
}

# Output the bucket name
output "bucket_name" {
  value = google_storage_bucket.my_bucket.name
}
