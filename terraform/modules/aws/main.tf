/**
 * # AWS Lightsail module
 *
 * This module deploys the OIOIO MCP Agent to AWS Lightsail.
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
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_size" {
  description = "Lightsail instance size"
  type        = string
  default     = "medium"
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

provider "aws" {
  region = var.region
}

# Create Lightsail instance
resource "aws_lightsail_instance" "mcp_agent" {
  name              = module.base.name_prefix
  availability_zone = "${var.region}a"
  blueprint_id      = "ubuntu_20_04"
  bundle_id         = "medium_2_0"
  key_pair_name     = aws_lightsail_key_pair.mcp_agent.name
  
  tags = module.base.tags
}

# Create Lightsail key pair
resource "aws_lightsail_key_pair" "mcp_agent" {
  name       = "${module.base.name_prefix}-key"
  public_key = var.ssh_public_key
}

# Open ports
resource "aws_lightsail_instance_public_ports" "mcp_agent" {
  instance_name = aws_lightsail_instance.mcp_agent.name

  port_info {
    protocol  = "tcp"
    from_port = 22
    to_port   = 22
  }

  port_info {
    protocol  = "tcp"
    from_port = 80
    to_port   = 80
  }

  port_info {
    protocol  = "tcp"
    from_port = 443
    to_port   = 443
  }
}

# Provisioning connection
resource "null_resource" "provisioner" {
  depends_on = [aws_lightsail_instance.mcp_agent, aws_lightsail_instance_public_ports.mcp_agent]
  
  # Trigger re-provisioning when any of these change
  triggers = {
    instance_id = aws_lightsail_instance.mcp_agent.id
    script_hash = sha256(module.base.install_script)
    config_hash = sha256(module.base.configure_script)
  }

  # Connection details for SSH
  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = var.ssh_private_key
    host        = aws_lightsail_instance.mcp_agent.public_ip_address
  }

  # Install the application
  provisioner "remote-exec" {
    inline = [
      "echo 'Starting installation...'",
      "sudo -E bash -c 'cat > /tmp/install.sh << \"EOL\"\n${module.base.install_script}\nEOL\n'",
      "sudo chmod +x /tmp/install.sh",
      "sudo /tmp/install.sh",
      "echo 'Installation complete!'"
    ]
  }
  
  # Configure the application
  provisioner "remote-exec" {
    inline = [
      "echo 'Starting configuration...'",
      "sudo -E bash -c 'cat > /tmp/configure.sh << \"EOL\"\n${module.base.configure_script}\nEOL\n'",
      "sudo chmod +x /tmp/configure.sh",
      "sudo /tmp/configure.sh",
      "echo 'Configuration complete!'"
    ]
  }
}

# Create static IP if needed
resource "aws_lightsail_static_ip" "mcp_agent" {
  count = var.domain_name != "" ? 1 : 0
  
  name = "${module.base.name_prefix}-ip"
}

# Attach static IP if created
resource "aws_lightsail_static_ip_attachment" "mcp_agent" {
  count = var.domain_name != "" ? 1 : 0
  
  static_ip_name = aws_lightsail_static_ip.mcp_agent[0].name
  instance_name  = aws_lightsail_instance.mcp_agent.name
}

# Outputs
output "public_ip" {
  description = "Public IP address of the Lightsail instance"
  value       = var.domain_name != "" ? aws_lightsail_static_ip.mcp_agent[0].ip_address : aws_lightsail_instance.mcp_agent.public_ip_address
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i <path_to_private_key> ubuntu@${var.domain_name != "" ? aws_lightsail_static_ip.mcp_agent[0].ip_address : aws_lightsail_instance.mcp_agent.public_ip_address}"
}

output "application_url" {
  description = "URL to access the application"
  value       = var.domain_name != "" ? "http://${var.domain_name}" : "http://${aws_lightsail_instance.mcp_agent.public_ip_address}"
}