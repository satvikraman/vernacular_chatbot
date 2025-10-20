# terraform/main.tf

# 1. DEFINE VARIABLES
# --------------------------------------------------------------------------------

variable "project_id" {
  description = "The GCP project ID to deploy the function to."
  type        = string
}

variable "region" {
  description = "The GCP region to deploy the function (e.g., us-central1)."
  type        = string
  default     = "us-central1"
}

variable "function_name" {
  description = "The desired name for the Cloud Function."
  type        = string
  default     = "vernacular-chatbot-function"
}

variable "entry_point" {
  description = "The name of the Python function to execute (from main.py)."
  type        = string
  default     = "hello_world"
}


# 2. PROVIDER CONFIGURATION
# --------------------------------------------------------------------------------

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket  = "vernacular-voice-bot-tf-state"
    prefix  = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "cloud_run" {
  project = var.project_id
  service = "run.googleapis.com"
}

# 3. CLOUD STORAGE BUCKET FOR SOURCE CODE
# --------------------------------------------------------------------------------

# Google recommends creating a new bucket for each function deployment region.
resource "google_storage_bucket" "source_bucket" {
  name          = "${var.project_id}-gcf-source-${var.region}"
  location      = var.region
  force_destroy = true # Allows Terraform to destroy the bucket even if it has files
  uniform_bucket_level_access = true
}

# 4. UPLOAD FUNCTION SOURCE CODE
# --------------------------------------------------------------------------------

# Upload the local zip file to the bucket.
resource "google_storage_bucket_object" "archive" {
  name   = "source-${timestamp()}.zip" # Use timestamp for unique object name on every deploy
  bucket = google_storage_bucket.source_bucket.name
  source = "./telegram_source.zip" # This is the file you created in Step 1
}

# 5. CREATE SERVICE ACCOUNT FOR THE FUNCTION
# --------------------------------------------------------------------------------

resource "google_service_account" "sa_for_function" {
  project      = var.project_id
  account_id   = "sa-voice-bot"
  display_name = "Service Account for Chatbot Function Runtime"
}

# 6. DEPLOY CLOUD FUNCTION (GENERATION 2)
# --------------------------------------------------------------------------------

resource "google_cloudfunctions2_function" "python_function" {
  name     = var.function_name
  location = var.region
  project  = var.project_id

  depends_on = [google_project_service.cloud_run]

  # Defines the source code location in Google Cloud Storage
  build_config {
    runtime     = "python312" # Use the latest stable runtime
    entry_point = var.entry_point
    source {
      storage_source {
        bucket = google_storage_bucket.source_bucket.name
        object = google_storage_bucket_object.archive.name
      }
    }
  }

  # Defines the function's runtime settings (memory, timeout, etc.)
  service_config {
    max_instance_count      = 3
    min_instance_count      = 0
    available_memory        = "256Mi"
    ingress_settings        = "ALLOW_ALL"
    service_account_email   = google_service_account.sa_for_function.email
    timeout_seconds         = 60
  }
}

resource "google_project_iam_member" "function_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.sa_for_function.email}"
}

# 7. OUTPUT THE FUNCTION URL
# --------------------------------------------------------------------------------

output "function_url" {
  description = "The URL of the deployed Cloud Function."
  value       = google_cloudfunctions2_function.python_function.service_config[0].uri
}

# 8. ALLOW PUBLIC/UNAUTHENTICATED ACCESS
# --------------------------------------------------------------------------------

resource "google_cloud_run_v2_service_iam_member" "allow_unauthenticated" {
  # Note: The GCF Gen 2 IAM policy is applied to the underlying Cloud Run service.
  # We reference the service name computed from the function resource.
  location = google_cloudfunctions2_function.python_function.location
  name     = google_cloudfunctions2_function.python_function.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}