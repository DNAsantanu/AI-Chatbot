# ============================================
# AI ChatBot — GCP Infrastructure (Terraform)
# Cloud Run, Artifact Registry, IAM, Secret Manager
# ============================================

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ──────────────────────────────────────────────
# Enable Required APIs
# ──────────────────────────────────────────────

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "logging.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}

# ──────────────────────────────────────────────
# Artifact Registry — Container Image Repository
# ──────────────────────────────────────────────

resource "google_artifact_registry_repository" "chatbot" {
  location      = var.gcp_region
  repository_id = "${var.project_name}-repo"
  description   = "Docker images for AI ChatBot"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }

  labels = var.labels

  depends_on = [google_project_service.apis]
}

# ──────────────────────────────────────────────
# Secret Manager — API Keys
# ──────────────────────────────────────────────

resource "google_secret_manager_secret" "groq_api_key" {
  secret_id = "${var.project_name}-groq-api-key"

  replication {
    auto {}
  }

  labels     = var.labels
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "tavily_api_key" {
  secret_id = "${var.project_name}-tavily-api-key"

  replication {
    auto {}
  }

  labels     = var.labels
  depends_on = [google_project_service.apis]
}

# ──────────────────────────────────────────────
# IAM — Cloud Run Service Account
# ──────────────────────────────────────────────

resource "google_service_account" "cloud_run" {
  account_id   = "${var.project_name}-runner"
  display_name = "AI ChatBot Cloud Run Service Account"
}

# Allow Cloud Run SA to access secrets
resource "google_secret_manager_secret_iam_member" "groq_access" {
  secret_id = google_secret_manager_secret.groq_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "tavily_access" {
  secret_id = google_secret_manager_secret.tavily_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Allow Cloud Run SA to write logs
resource "google_project_iam_member" "logging" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ──────────────────────────────────────────────
# Cloud Run — Backend Service
# ──────────────────────────────────────────────

resource "google_cloud_run_v2_service" "backend" {
  name     = "${var.project_name}-backend"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.chatbot.repository_id}/${var.project_name}-backend:latest"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = var.backend_cpu
          memory = var.backend_memory
        }
      }

      env {
        name  = "BACKEND_HOST"
        value = "0.0.0.0"
      }

      env {
        name  = "BACKEND_PORT"
        value = "8000"
      }

      env {
        name = "GROQ_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.groq_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "TAVILY_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.tavily_api_key.secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        period_seconds = 30
      }
    }
  }

  labels     = var.labels
  depends_on = [google_project_service.apis]
}

# ──────────────────────────────────────────────
# Cloud Run — Frontend Service
# ──────────────────────────────────────────────

resource "google_cloud_run_v2_service" "frontend" {
  name     = "${var.project_name}-frontend"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.chatbot.repository_id}/${var.project_name}-frontend:latest"

      ports {
        container_port = 8501
      }

      resources {
        limits = {
          cpu    = var.frontend_cpu
          memory = var.frontend_memory
        }
      }

      env {
        name  = "BACKEND_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      startup_probe {
        http_get {
          path = "/_stcore/health"
          port = 8501
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
    }
  }

  labels     = var.labels
  depends_on = [google_project_service.apis]
}

# ──────────────────────────────────────────────
# IAM — Make Cloud Run services publicly accessible
# ──────────────────────────────────────────────

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.gcp_region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.gcp_region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
