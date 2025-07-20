/**
 * # DigitalOcean module
 *
 * This module deploys the OIOIO MCP Agent to DigitalOcean.
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
  description = "DigitalOcean region"
  type        = string
  default     = "nyc1"
}

variable "instance_size" {
  description = "Droplet size"
  type        = string
  default     = "s-2vcpu-2gb"
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

variable "do_token" {
  description = "DigitalOcean API token"
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

# Configure the DigitalOcean Provider
provider "digitalocean" {
  token = var.do_token
}

# Create SSH key
resource "digitalocean_ssh_key" "mcp_agent" {
  name       = "${module.base.name_prefix}-key"
  public_key = var.ssh_public_key
}

# Create a droplet
resource "digitalocean_droplet" "mcp_agent" {
  name     = module.base.name_prefix
  image    = "ubuntu-20-04-x64"
  region   = var.region
  size     = var.instance_size
  ssh_keys = [digitalocean_ssh_key.mcp_agent.fingerprint]
  
  tags = [var.environment, var.project, "terraform"]
}

# Create project
resource "digitalocean_project" "mcp_agent" {
  name        = module.base.name_prefix
  description = "OIOIO MCP Agent project for ${var.environment} environment"
  purpose     = "Web Application"
  environment = var.environment
  resources   = [digitalocean_droplet.mcp_agent.urn]
}

# Provision the droplet
resource "null_resource" "provisioner" {
  depends_on = [digitalocean_droplet.mcp_agent]
  
  # Trigger re-provisioning when any of these change
  triggers = {
    droplet_id  = digitalocean_droplet.mcp_agent.id
    script_hash = sha256(module.base.install_script)
    config_hash = sha256(module.base.configure_script)
  }

  # Connection details for SSH
  connection {
    type        = "ssh"
    user        = "root"
    private_key = var.ssh_private_key
    host        = digitalocean_droplet.mcp_agent.ipv4_address
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
resource "digitalocean_record" "www" {
  count = var.domain_name != "" ? 1 : 0
  
  domain = var.domain_name
  type   = "A"
  name   = "@"
  value  = digitalocean_droplet.mcp_agent.ipv4_address
}

# Create firewall
resource "digitalocean_firewall" "mcp_agent" {
  name = "${module.base.name_prefix}-firewall"

  droplet_ids = [digitalocean_droplet.mcp_agent.id]

  # SSH
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # HTTP
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # HTTPS
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  # Allow all outbound traffic
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  
  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# Outputs
output "public_ip" {
  description = "Public IP address of the droplet"
  value       = digitalocean_droplet.mcp_agent.ipv4_address
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i <path_to_private_key> root@${digitalocean_droplet.mcp_agent.ipv4_address}"
}

output "application_url" {
  description = "URL to access the application"
  value       = var.domain_name != "" ? "http://${var.domain_name}" : "http://${digitalocean_droplet.mcp_agent.ipv4_address}"
}