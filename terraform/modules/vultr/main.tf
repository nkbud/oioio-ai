/**
 * # Vultr module
 *
 * This module deploys the OIOIO MCP Agent to Vultr.
 */

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project" {
  description = "Project name"
  type        = string
}

variable "region" {
  description = "Vultr region"
  type        = string
  default     = "ewr"  # New Jersey
}

variable "instance_size" {
  description = "Instance plan"
  type        = string
  default     = "vc2-2c-4gb"  # 2 CPU, 4GB RAM
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

variable "ssh_private_key" {
  description = "SSH private key for provisioning"
  type        = string
  sensitive   = true
}

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
  default     = ""
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openrouter_api_key" {
  description = "OpenRouter API key"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "vultr_api_key" {
  description = "Vultr API key"
  type        = string
  sensitive   = true
}

# Call base module
module "base" {
  source = "../base"
  
  environment         = var.environment
  project             = var.project
  region              = var.region
  instance_size       = var.instance_size
  ssh_public_key      = var.ssh_public_key
  ssh_private_key     = var.ssh_private_key
  database_password   = var.database_password
  jwt_secret          = var.jwt_secret
  session_secret      = var.session_secret
  google_client_id    = var.google_client_id
  google_client_secret = var.google_client_secret
  openrouter_api_key  = var.openrouter_api_key
  domain_name         = var.domain_name
}

# Configure the Vultr Provider
provider "vultr" {
  api_key = var.vultr_api_key
}

# Create SSH key
resource "vultr_ssh_key" "mcp_agent" {
  name    = "${module.base.name_prefix}-key"
  ssh_key = var.ssh_public_key
}

# Create instance
resource "vultr_instance" "mcp_agent" {
  plan       = var.instance_size
  region     = var.region
  os_id      = 387  # Ubuntu 20.04 LTS x64
  hostname   = module.base.name_prefix
  label      = module.base.name_prefix
  ssh_key_ids = [vultr_ssh_key.mcp_agent.id]
  
  tags = [var.environment, var.project, "terraform"]
}

# Provision the instance
resource "null_resource" "provisioner" {
  depends_on = [vultr_instance.mcp_agent]
  
  # Trigger re-provisioning when any of these change
  triggers = {
    instance_id = vultr_instance.mcp_agent.id
    script_hash = sha256(module.base.install_script)
    config_hash = sha256(module.base.configure_script)
  }

  # Wait for instance to become available
  provisioner "local-exec" {
    command = "sleep 60"  # Wait for instance to finish booting
  }

  # Connection details for SSH
  connection {
    type        = "ssh"
    user        = "root"
    private_key = var.ssh_private_key
    host        = vultr_instance.mcp_agent.main_ip
  }

  # Install the application
  provisioner "remote-exec" {
    inline = [
      "echo 'Starting installation...'",
      "cat > /tmp/install.sh << 'EOL'\n${module.base.install_script}\nEOL",
      "chmod +x /tmp/install.sh",
      "/tmp/install.sh",
      "echo 'Installation complete!'"
    ]
  }
  
  # Configure the application
  provisioner "remote-exec" {
    inline = [
      "echo 'Starting configuration...'",
      "cat > /tmp/configure.sh << 'EOL'\n${module.base.configure_script}\nEOL",
      "chmod +x /tmp/configure.sh",
      "/tmp/configure.sh",
      "echo 'Configuration complete!'"
    ]
  }
}

# Create DNS record if domain is provided
resource "vultr_dns_record" "www" {
  count = var.domain_name != "" ? 1 : 0
  
  domain  = var.domain_name
  type    = "A"
  name    = "@"
  data    = vultr_instance.mcp_agent.main_ip
  ttl     = 3600
}

# Outputs
output "public_ip" {
  description = "Public IP address of the instance"
  value       = vultr_instance.mcp_agent.main_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i <path_to_private_key> root@${vultr_instance.mcp_agent.main_ip}"
}

output "application_url" {
  description = "URL to access the application"
  value       = var.domain_name != "" ? "http://${var.domain_name}" : "http://${vultr_instance.mcp_agent.main_ip}"
}