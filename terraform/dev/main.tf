terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.20"
    }
  }

  # ── Stan Terraform w GCS ────────────────────────────────────────────────────
  # Odblokuj po uruchomieniu scripts/gcp_bootstrap.sh i wpisz swój PROJECT_ID:
  #
  # backend "gcs" {
  #   bucket = "<PROJECT_ID>-tfstate"
  #   prefix = "terraform/dev"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "diag1" {
  source     = "../modules/diag1"
  project_id = var.project_id
  region     = var.region
  prefix     = "diag1-dev"
  repo_name  = var.repo_name

  database_url    = var.database_url
  gemini_api_key  = var.gemini_api_key
  vertex_location = var.vertex_location
  vertex_model    = var.vertex_model
  backend_image   = var.backend_image
  frontend_image  = var.frontend_image

  domain                            = var.domain
  frontend_access_password          = var.frontend_access_password
  frontend_access_cookie_secret     = var.frontend_access_cookie_secret
  frontend_access_session_ttl_hours = var.frontend_access_session_ttl_hours
}
