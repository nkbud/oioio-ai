/**
 * # Development Environment
 *
 * This configuration deploys the OIOIO MCP Agent to a development environment.
 */

# Choose the provider you want to use
module "mcp_agent" {
  # Uncomment the provider you want to use:
  source = "../../modules/digitalocean"  # DigitalOcean (default)
  # source = "../../modules/aws"         # AWS Lightsail
  # source = "../../modules/vultr"       # Vultr
  
  # Common variables
  environment       = "dev"
  project           = "oioio-mcp-agent"
  
  # Provider-specific variables
  region            = "nyc1"  # Update based on provider
  instance_size     = "s-1vcpu-2gb"  # Adjust based on provider
  
  # Authentication
  ssh_public_key    = file("~/.ssh/id_rsa.pub")  # Update path to your SSH public key
  ssh_private_key   = file("~/.ssh/id_rsa")      # Update path to your SSH private key
  
  # Secrets (use environment variables in production)
  database_password = "dev_password_change_me"
  jwt_secret        = "dev_jwt_secret_change_me"
  session_secret    = "dev_session_secret_change_me"
  
  # OAuth (optional)
  google_client_id     = ""  # Add your Google client ID if using OAuth
  google_client_secret = ""  # Add your Google client secret if using OAuth
  
  # API keys
  openrouter_api_key   = "not_a_real_key"  # Add your OpenRouter API key
  
  # Domain name (optional)
  domain_name       = ""  # Add your domain name if you have one
  
  # DigitalOcean-specific variables
  do_token          = "not_a_real_token"  # Required for DigitalOcean
  
  # Uncomment these when using other providers
  # AWS Lightsail-specific variables
  # No additional variables needed
  
  # Vultr-specific variables
  # vultr_api_key     = "not_a_real_key"  # Required for Vultr
}

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