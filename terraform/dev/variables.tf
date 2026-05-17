variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "repo_name" {
  type = string
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

variable "domain" {
  type        = string
  description = "Własna domena, np. dev.app.example.com"
}

variable "backend_image" {
  type    = string
  default = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "frontend_image" {
  type    = string
  default = "us-docker.pkg.dev/cloudrun/container/hello"
}


variable "frontend_access_password" {
  type      = string
  default   = ""
  sensitive = true
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
