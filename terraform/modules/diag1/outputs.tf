output "backend_url" {
  description = "Cloud Run backend URL (wewnętrzny – dostępny tylko przez LB)"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "Cloud Run frontend URL (wewnętrzny – dostępny tylko przez LB)"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "repo_name" {
  description = "Nazwa repozytorium Artifact Registry"
  value       = google_artifact_registry_repository.repo.repository_id
}

output "lb_ip" {
  description = "Zewnętrzny adres IP Load Balancera – dodaj jako rekord A DNS dla swojej domeny"
  value       = google_compute_global_address.lb_ip.address
}

output "public_url" {
  description = "Publiczny adres URL aplikacji (po skonfigurowaniu DNS)"
  value       = "https://${var.domain}"
}
