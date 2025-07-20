/**
 * # Production Environment
 *
 * This configuration deploys the OIOIO MCP Agent to a production environment.
 */

# Choose the provider you want to use
module "mcp_agent" {
  # Uncomment the provider you want to use:
  source = "../../modules/digitalocean"  # DigitalOcean (default)
  # source = "../../modules/aws"         # AWS Lightsail
  # source = "../../modules/vultr"       # Vultr
  
  # Common variables
  environment       = "prod"
  project           = "oioio-mcp-agent"
  
  # Provider-specific variables
  region            = "nyc1"  # Update based on provider
  instance_size     = "s-2vcpu-4gb"  # Adjust based on provider (higher for production)
  
  # Authentication
  ssh_public_key    = file("~/.ssh/id_rsa.pub")  # Update path to your SSH public key
  ssh_private_key   = file("~/.ssh/id_rsa")      # Update path to your SSH private key
  
  # Secrets (use environment variables in production)
  database_password = var.database_password
  jwt_secret        = var.jwt_secret
  session_secret    = var.session_secret
  
  # OAuth (required for production)
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
  
  # API keys
  openrouter_api_key   = var.openrouter_api_key
  
  # Domain name (required for production)
  domain_name       = var.domain_name
  
  # DigitalOcean-specific variables
  do_token          = var.do_token  # Required for DigitalOcean
  
  # Uncomment these when using other providers
  # AWS Lightsail-specific variables
  # No additional variables needed
  
  # Vultr-specific variables
  # vultr_api_key     = var.vultr_api_key  # Required for Vultr
}

# Variables for production (use terraform.tfvars or environment variables)
variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "session_secret" {
  description = "Session secret key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
}

variable "openrouter_api_key" {
  description = "OpenRouter API key"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

# Uncomment when using Vultr
# variable "vultr_api_key" {
#   description = "Vultr API key"
#   type        = string
#   sensitive   = true
# }

output "public_ip" {
  description = "Public IP address of the instance"
  value       = module.mcp_agent.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = module.mcp_agent.ssh_command
}

output "application_url" {
  description = "URL to access the application"
  value       = module.mcp_agent.application_url
}