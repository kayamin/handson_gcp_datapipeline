resource "google_storage_bucket" "terraform-state-store" {
  name     = "handson-datapipeline-tfstate"
  location = "us-west1"
  storage_class = "REGIONAL"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 5
    }
  }
}

terraform {
  backend "gcs" {
    bucket = "handson-datapipeline-tfstate"
  }
}