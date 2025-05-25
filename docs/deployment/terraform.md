# Terraform Deployment Guide

This guide explains how to deploy the OIOIO MCP Agent to various cloud providers using Terraform.

## Overview

The repository includes Terraform configurations for deploying to:

- DigitalOcean
- AWS Lightsail
- Vultr

Each configuration sets up a complete environment including:

- Virtual server instance
- Firewall configuration
- Database (local PostgreSQL)
- Nginx reverse proxy
- Systemd service for the API server
- Docker for MCP services

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) (v1.0.0+)
- SSH key pair
- API tokens for your cloud provider
- Domain name (optional)

## Deployment Structure

```
terraform/
├── modules/
│   ├── base/         # Common configurations
│   ├── aws/          # AWS Lightsail specific
│   ├── digitalocean/ # DigitalOcean specific
│   └── vultr/        # Vultr specific
└── environments/
    ├── dev/          # Development environment
    └── prod/         # Production environment
```

## Quick Start

### 1. Configure Environment Variables

Create a `.env.terraform` file:

```bash
# Provider API tokens
export TF_VAR_do_token="your_digitalocean_token"
export TF_VAR_vultr_api_key="your_vultr_api_key"

# Secrets
export TF_VAR_database_password="secure_database_password"
export TF_VAR_jwt_secret="secure_jwt_secret"
export TF_VAR_session_secret="secure_session_secret"
export TF_VAR_openrouter_api_key="your_openrouter_api_key"

# OAuth (for production)
export TF_VAR_google_client_id="your_google_client_id"
export TF_VAR_google_client_secret="your_google_client_secret"

# Domain (for production)
export TF_VAR_domain_name="your-domain.com"
```

Load these variables:

```bash
source .env.terraform
```

### 2. Choose Environment and Provider

For development:

```bash
cd terraform/environments/dev
```

For production:

```bash
cd terraform/environments/prod
```

Edit `main.tf` to select your cloud provider:

```hcl
module "mcp_agent" {
  source = "../../modules/digitalocean"  # Change to aws or vultr
  
  # ...other configuration...
}
```

### 3. Initialize and Apply

```bash
terraform init
terraform plan
terraform apply
```

### 4. Access Your Deployment

After deployment completes, Terraform will output:

- Public IP address
- SSH command
- Application URL

Example:
```
Outputs:

application_url = "http://203.0.113.10"
public_ip = "203.0.113.10"
ssh_command = "ssh -i ~/.ssh/id_rsa root@203.0.113.10"
```

## Customizing the Deployment

### Instance Size

Adjust the instance size based on your needs:

```hcl
# For DigitalOcean
instance_size = "s-2vcpu-4gb"  # 2 CPUs, 4GB RAM

# For AWS Lightsail
instance_size = "medium"  # Medium instance

# For Vultr
instance_size = "vc2-2c-4gb"  # 2 CPUs, 4GB RAM
```

### Region

Choose a region close to your users:

```hcl
# For DigitalOcean
region = "nyc1"  # New York

# For AWS Lightsail
region = "us-east-1"  # US East (N. Virginia)

# For Vultr
region = "ewr"  # New Jersey
```

### Domain Name

For production deployments, configure a domain name:

```hcl
domain_name = "mcp-agent.example.com"
```

This will:
- Set up DNS records (if using DigitalOcean or Vultr with domain)
- Configure Nginx for the domain
- Prepare for SSL certificates

## Advanced Configuration

### Database Configuration

By default:
- Development uses SQLite
- Production uses PostgreSQL

To use an external database, modify the `database_url` in the configuration script.

### SSL Certificates

For HTTPS:

1. SSH into your server
2. Install Certbot:
   ```bash
   apt-get install certbot python3-certbot-nginx
   ```
3. Generate certificates:
   ```bash
   certbot --nginx -d your-domain.com
   ```

### Custom Environment Variables

Add custom environment variables in the base module's `common_env_vars` locals block.

## CI/CD Integration

The repository includes GitHub Actions workflows for automated deployment:

- `.github/workflows/deploy.yml`: Manual deployment
- `.github/workflows/publish.yml`: Deployment on release

Configure GitHub secrets matching the Terraform variables above to enable these workflows.

## Troubleshooting

### SSH Connection Issues

- Check that your SSH key is correctly configured
- Verify that the security group/firewall allows SSH connections
- Wait a few minutes after creation for the instance to fully initialize

### Application Not Starting

SSH into the instance and check:

```bash
# Check service status
systemctl status mcp-agent

# View logs
journalctl -u mcp-agent -n 100

# Check configuration
cat /opt/oioio-mcp-agent/.env
```

### Database Issues

```bash
# For PostgreSQL:
sudo -u postgres psql -c "SELECT version();"
sudo -u postgres psql -c "\\l"  # List databases
```

## Next Steps

- Set up [CI/CD Pipelines](./cicd.md)
- Configure [Custom Domain and SSL](./ssl_setup.md)
- Learn about [Monitoring and Maintenance](./monitoring.md)