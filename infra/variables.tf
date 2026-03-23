# ============================================
# AI ChatBot — Terraform Variables (GCP)
# ============================================

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ai-chatbot"
}

# ── Cloud Run Sizing ──

variable "min_instances" {
  description = "Minimum Cloud Run instances (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 3
}

variable "backend_cpu" {
  description = "Backend CPU limit"
  type        = string
  default     = "1"
}

variable "backend_memory" {
  description = "Backend memory limit"
  type        = string
  default     = "512Mi"
}

variable "frontend_cpu" {
  description = "Frontend CPU limit"
  type        = string
  default     = "1"
}

variable "frontend_memory" {
  description = "Frontend memory limit"
  type        = string
  default     = "512Mi"
}

# ── Labels ──

variable "labels" {
  description = "Resource labels"
  type        = map(string)
  default = {
    project     = "ai-chatbot"
    environment = "production"
    managed-by  = "terraform"
  }
}
