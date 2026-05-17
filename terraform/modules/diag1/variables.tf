variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "prefix" {
  type = string
}

variable "repo_name" {
  type = string
}

variable "backend_image" {
  type    = string
  default = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "frontend_image" {
  type    = string
  default = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "database_url" {
  type      = string
  sensitive = true
}

variable "gemini_api_key" {
  type      = string
  default   = ""
  sensitive = true
}

variable "vertex_location" {
  type    = string
  default = "europe-west3"
}

variable "vertex_model" {
  type    = string
  default = "gemini-2.5-flash"
}

# ── BEZPIECZEŃSTWO – domena i ruch publiczny przez Cloud Load Balancer ─────

variable "domain" {
  type        = string
  description = "Własna domena dla aplikacji, np. app.example.com"
}

variable "frontend_access_password" {
  type    = string
  default = ""
}

variable "frontend_access_cookie_secret" {
  type      = string
  default   = ""
  sensitive = true
}

variable "frontend_access_session_ttl_hours" {
  type    = number
  default = 12
}
