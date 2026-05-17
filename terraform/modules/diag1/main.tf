locals {
  backend_service_name  = "${var.prefix}-backend"
  frontend_service_name = "${var.prefix}-frontend"
}

# ---------------------------------------------------------
# 1. API
# ---------------------------------------------------------
resource "google_project_service" "api" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

# ---------------------------------------------------------
# 2. ARTIFACT REGISTRY
# ---------------------------------------------------------
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.repo_name
  format        = "DOCKER"
  depends_on    = [google_project_service.api]
}

# ---------------------------------------------------------
# 3. CLOUD RUN SERVICES
#    ingress = INTERNAL_LOAD_BALANCER → akceptuje ruch
#    tylko z Load Balancera, nie bezpośrednio z internetu
# ---------------------------------------------------------
resource "google_cloud_run_v2_service" "backend" {
  name     = local.backend_service_name
  location = var.region

  # BEZPIECZEŃSTWO: tylko ruch z LB; żaden zewnętrzny adres
  # nie może wywołać Cloud Run bezpośrednio
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    max_instance_request_concurrency = 8

    containers {
      image = var.backend_image

      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }

      env {
        name  = "AI_PROVIDER"
        value = "vertex"
      }

      env {
        name  = "VERTEX_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "VERTEX_LOCATION"
        value = var.vertex_location
      }

      env {
        name  = "VERTEX_MODEL"
        value = var.vertex_model
      }

      env {
        name  = "CORS_ORIGINS"
        value = "https://${var.domain}"
      }

      env {
        name  = "FRONTEND_ACCESS_PASSWORD"
        value = var.frontend_access_password
      }

      env {
        name  = "FRONTEND_ACCESS_COOKIE_SECRET"
        value = var.frontend_access_cookie_secret
      }

      env {
        name  = "FRONTEND_ACCESS_SESSION_TTL_HOURS"
        value = tostring(var.frontend_access_session_ttl_hours)
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }

  depends_on = [google_project_service.api]
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = local.frontend_service_name
  location = var.region

  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    containers {
      image = var.frontend_image
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }

  depends_on = [google_project_service.api]
}

# Publiczny dostęp do backendu przez Cloud Run (ruch przechodzi przez LB)
resource "google_cloud_run_v2_service_iam_member" "backend_public_invoker" {
  name     = google_cloud_run_v2_service.backend.name
  location = google_cloud_run_v2_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Publiczny dostęp do frontendu przez Cloud Run (ruch przechodzi przez LB)
resource "google_cloud_run_v2_service_iam_member" "frontend_public_invoker" {
  name     = google_cloud_run_v2_service.frontend.name
  location = google_cloud_run_v2_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ---------------------------------------------------------
# 4. ZEWNĘTRZNY ADRES IP (dla Load Balancera)
# ---------------------------------------------------------
resource "google_compute_global_address" "lb_ip" {
  name       = "${var.prefix}-lb-ip"
  depends_on = [google_project_service.api]
}

# ---------------------------------------------------------
# 5. CERTYFIKAT SSL (zarządzany przez Google)
#    Google automatycznie wyda i odnowi certyfikat dla domeny.
#    Wymaga aktywnego rekordu DNS A → lb_ip.address
# ---------------------------------------------------------
resource "google_compute_managed_ssl_certificate" "ssl_cert" {
  name = "${var.prefix}-ssl-cert"

  managed {
    domains = [var.domain]
  }

  depends_on = [google_project_service.api]
}

# ---------------------------------------------------------
# 6. SERVERLESS NEGs
#    Łączą Load Balancer z Cloud Run bez statycznych instancji
# ---------------------------------------------------------
resource "google_compute_region_network_endpoint_group" "backend_neg" {
  name                  = "${var.prefix}-backend-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.backend.name
  }

  depends_on = [google_project_service.api]
}

resource "google_compute_region_network_endpoint_group" "frontend_neg" {
  name                  = "${var.prefix}-frontend-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.frontend.name
  }

  depends_on = [google_project_service.api]
}

# ---------------------------------------------------------
# 7. BACKEND SERVICES
# ---------------------------------------------------------
resource "google_compute_backend_service" "backend_bs" {
  name = "${var.prefix}-backend-bs"

  backend {
    group = google_compute_region_network_endpoint_group.backend_neg.id
  }
}

resource "google_compute_backend_service" "frontend_bs" {
  name = "${var.prefix}-frontend-bs"

  backend {
    group = google_compute_region_network_endpoint_group.frontend_neg.id
  }
}

# ---------------------------------------------------------
# 8. URL MAP – routing oparty na ścieżce
#     /api/*   → backend (FastAPI)
#     /*       → frontend (Vue.js)
# ---------------------------------------------------------
resource "google_compute_url_map" "url_map" {
  name            = "${var.prefix}-url-map"
  default_service = google_compute_backend_service.frontend_bs.id

  host_rule {
    hosts        = [var.domain]
    path_matcher = "paths"
  }

  path_matcher {
    name            = "paths"
    default_service = google_compute_backend_service.frontend_bs.id

    path_rule {
      # Ścieżki API FastAPI + dokumentacja Swagger
      paths   = ["/api", "/api/*", "/api/healthz", "/docs", "/openapi.json", "/redoc"]
      service = google_compute_backend_service.backend_bs.id
    }
  }
}

# ---------------------------------------------------------
# 9. HTTPS PROXY + PRZEKIEROWANIE HTTP→HTTPS
# ---------------------------------------------------------
resource "google_compute_target_https_proxy" "https_proxy" {
  name             = "${var.prefix}-https-proxy"
  url_map          = google_compute_url_map.url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.ssl_cert.id]
}

resource "google_compute_global_forwarding_rule" "https_rule" {
  name       = "${var.prefix}-https-rule"
  target     = google_compute_target_https_proxy.https_proxy.id
  port_range = "443"
  ip_address = google_compute_global_address.lb_ip.id
}

# Przekierowanie HTTP (port 80) → HTTPS (port 443)
resource "google_compute_url_map" "http_redirect" {
  name = "${var.prefix}-http-redirect"

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

resource "google_compute_target_http_proxy" "http_proxy" {
  name    = "${var.prefix}-http-proxy"
  url_map = google_compute_url_map.http_redirect.id
}

# ---------------------------------------------------------
# 10. PUBLIC ACCESS GATE
#     Całość zabezpieczenia frontendu realizowana jest po stronie samej aplikacji.
# ---------------------------------------------------------
resource "google_compute_global_forwarding_rule" "http_rule" {
  name       = "${var.prefix}-http-rule"
  target     = google_compute_target_http_proxy.http_proxy.id
  port_range = "80"
  ip_address = google_compute_global_address.lb_ip.id
}
