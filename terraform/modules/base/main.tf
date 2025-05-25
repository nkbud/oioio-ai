/**
 * # Base module
 *
 * This module contains common variables and outputs for all cloud deployments.
 */

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project" {
  description = "Project name"
  type        = string
  default     = "oioio-mcp-agent"
}

variable "region" {
  description = "Cloud region"
  type        = string
}

variable "instance_size" {
  description = "Instance size/type"
  type        = string
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

# Common tags
locals {
  tags = {
    Environment = var.environment
    Project     = var.project
    Terraform   = "true"
  }
  
  # Common name format
  name_prefix = "${var.project}-${var.environment}"
  
  # Common env vars
  common_env_vars = {
    MCP_ENV                = var.environment
    DATABASE_URL           = var.environment == "prod" ? "postgresql://mcp:${var.database_password}@localhost/mcp" : "sqlite:///./oioio_mcp_agent.db"
    JWT_SECRET             = var.jwt_secret
    SESSION_SECRET         = var.session_secret
    GOOGLE_CLIENT_ID       = var.google_client_id
    GOOGLE_CLIENT_SECRET   = var.google_client_secret
    OPENROUTER_API_KEY     = var.openrouter_api_key
  }
  
  # Common provisioning scripts
  install_script = <<-EOT
    #!/bin/bash
    set -e
    
    # Update and install dependencies
    apt-get update
    apt-get install -y python3 python3-pip python3-venv docker.io docker-compose nginx
    
    # Set up application directory
    mkdir -p /opt/oioio-mcp-agent
    
    # Set up Python environment
    python3 -m venv /opt/oioio-mcp-agent/venv
    /opt/oioio-mcp-agent/venv/bin/pip install --upgrade pip
    /opt/oioio-mcp-agent/venv/bin/pip install oioio-mcp-agent
    
    # Create systemd service
    cat > /etc/systemd/system/mcp-agent.service << 'EOF'
    [Unit]
    Description=OIOIO MCP Agent API Server
    After=network.target
    
    [Service]
    User=mcp
    WorkingDirectory=/opt/oioio-mcp-agent
    ExecStart=/opt/oioio-mcp-agent/venv/bin/python -m oioio_mcp_agent serve
    Restart=always
    RestartSec=5
    Environment="PATH=/opt/oioio-mcp-agent/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    
    [Install]
    WantedBy=multi-user.target
    EOF
    
    # Set up Nginx
    cat > /etc/nginx/sites-available/mcp-agent << 'EOF'
    server {
        listen 80;
        server_name _;
        
        location / {
            proxy_pass http://localhost:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    EOF
    
    ln -sf /etc/nginx/sites-available/mcp-agent /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Create mcp user
    useradd -m -s /bin/bash mcp || true
    chown -R mcp:mcp /opt/oioio-mcp-agent
    
    # Set up application config and environment
    mkdir -p /opt/oioio-mcp-agent/configs
    
    # Service will be started after configuration is deployed
    systemctl daemon-reload
    systemctl enable mcp-agent
    systemctl enable nginx
    systemctl restart nginx
  EOT
  
  configure_script = <<-EOT
    #!/bin/bash
    set -e
    
    # Create environment file
    cat > /opt/oioio-mcp-agent/.env << 'EOF'
    # Environment configuration
    MCP_ENV=${var.environment}
    
    # Database configuration
    DATABASE_URL=${var.environment == "prod" ? "postgresql://mcp:${var.database_password}@localhost/mcp" : "sqlite:///./oioio_mcp_agent.db"}
    
    # Authentication
    JWT_SECRET=${var.jwt_secret}
    SESSION_SECRET=${var.session_secret}
    
    # OAuth configuration
    GOOGLE_CLIENT_ID=${var.google_client_id}
    GOOGLE_CLIENT_SECRET=${var.google_client_secret}
    
    # API keys
    OPENROUTER_API_KEY=${var.openrouter_api_key}
    EOF
    
    # Create basic config
    cat > /opt/oioio-mcp-agent/configs/config.yaml << 'EOF'
    version: "1.0"
    
    # Core configuration
    core:
      knowledge_dir: knowledge
      checkpoint_dir: .prefect
      log_level: ${var.environment == "prod" ? "INFO" : "DEBUG"}
    
    # API configuration
    api:
      host: "0.0.0.0"
      port: 8000
      reload: ${var.environment == "prod" ? "false" : "true"}
      database_url: "${var.environment == "prod" ? "postgresql://mcp:${var.database_password}@localhost/mcp" : "sqlite:///./oioio_mcp_agent.db"}"
      jwt_secret: "${var.jwt_secret}"
      jwt_expire_minutes: 30
      session_secret: "${var.session_secret}"
      oauth:
        google_client_id: "${var.google_client_id}"
        google_client_secret: "${var.google_client_secret}"
    
    # Docker configuration
    docker:
      compose_file: docker-compose.yml
      services:
        - name: brave-search
          image: mcp/brave-search
          port: 8080
    EOF
    
    # Set permissions
    chown -R mcp:mcp /opt/oioio-mcp-agent
    
    # Initialize database if needed
    if [ "${var.environment}" == "prod" ]; then
      apt-get install -y postgresql postgresql-contrib
      systemctl enable postgresql
      systemctl start postgresql
      
      # Create database and user
      su - postgres -c "psql -c \"CREATE USER mcp WITH PASSWORD '${var.database_password}';\""
      su - postgres -c "psql -c \"CREATE DATABASE mcp OWNER mcp;\""
    fi
    
    # Initialize database schema
    su - mcp -c "cd /opt/oioio-mcp-agent && /opt/oioio-mcp-agent/venv/bin/python -m oioio_mcp_agent db upgrade"
    
    # Start the service
    systemctl restart mcp-agent
  EOT
}

output "common_env_vars" {
  description = "Common environment variables"
  value       = local.common_env_vars
  sensitive   = true
}

output "name_prefix" {
  description = "Common name prefix for resources"
  value       = local.name_prefix
}

output "tags" {
  description = "Common tags for all resources"
  value       = local.tags
}

output "install_script" {
  description = "Installation script for the MCP agent"
  value       = local.install_script
}

output "configure_script" {
  description = "Configuration script for the MCP agent"
  value       = local.configure_script
  sensitive   = true
}