output "backend_url" {
  value       = module.diag1.backend_url
  description = "Cloud Run backend URL (wewnętrzny)"
}

output "frontend_url" {
  value       = module.diag1.frontend_url
  description = "Cloud Run frontend URL (wewnętrzny)"
}

output "repo_name" {
  value = module.diag1.repo_name
}

output "lb_ip" {
  value       = module.diag1.lb_ip
  description = "Adres IP Load Balancera – dodaj rekord A DNS dla swojej domeny"
}

output "public_url" {
  value       = module.diag1.public_url
  description = "Publiczny URL aplikacji po skonfigurowaniu DNS"
}
