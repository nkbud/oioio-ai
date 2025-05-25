# CI/CD Pipeline Guide

This guide explains how to use the continuous integration and deployment pipelines for the OIOIO MCP Agent.

## Overview

The repository includes GitHub Actions workflows for:

1. **Continuous Integration**: Testing, linting, and package building
2. **Publishing**: Releasing packages to PyPI
3. **Deployment**: Automated deployment to cloud providers

## CI Workflow

The CI workflow (`ci.yml`) runs on every push and pull request to the main and develop branches.

### What It Does

- Runs tests with pytest
- Checks code quality with flake8
- Verifies type hints with mypy
- Builds the Python package
- Uploads build artifacts (for releases)

### Configuration

No additional configuration is needed for the CI workflow. It uses the repository's existing test setup.

## Publish Workflow

The publish workflow (`publish.yml`) runs when a new release is created on GitHub.

### What It Does

- Builds the Python package
- Publishes it to PyPI
- Optionally deploys to development or production environments

### Configuration

1. Create a PyPI API token at [pypi.org](https://pypi.org/manage/account/token/)
2. Add the token to GitHub repository secrets as `PYPI_API_TOKEN`
3. Configure environment variables for deployment if needed (see below)

### Creating a Release

1. On GitHub, go to the repository's **Releases** section
2. Click **Draft a new release**
3. Create a tag (e.g., `v1.0.0`)
4. Add release notes
5. Choose a release type:
   - **Pre-release** - Deploys to development environment
   - **Regular release** - Deploys to production environment

## Deploy Workflow

The deploy workflow (`deploy.yml`) can be manually triggered to deploy to any environment and cloud provider.

### What It Does

- Allows choosing environment (dev/prod) and provider (aws/digitalocean/vultr)
- Sets up Terraform for the chosen provider
- Deploys using the environment configuration
- Outputs connection details

### Configuration

Add the following GitHub repository secrets:

```
# SSH Keys
SSH_PRIVATE_KEY       # Your private SSH key for server access

# Database
DATABASE_PASSWORD     # Password for PostgreSQL database

# Authentication
JWT_SECRET            # Secret for JWT tokens
SESSION_SECRET        # Secret for session cookies

# API Keys
OPENROUTER_API_KEY    # OpenRouter API key

# OAuth (for production)
GOOGLE_CLIENT_ID      # Google OAuth client ID
GOOGLE_CLIENT_SECRET  # Google OAuth client secret

# Domain (for production)
DOMAIN_NAME           # Your domain name

# Provider-specific tokens
DO_TOKEN              # DigitalOcean API token
VULTR_API_KEY         # Vultr API key
```

### Running a Manual Deployment

1. Go to the **Actions** tab in your repository
2. Select the **Deploy** workflow
3. Click **Run workflow**
4. Choose:
   - **Environment**: `dev` or `prod`
   - **Cloud provider**: `digitalocean`, `aws`, or `vultr`
5. Click **Run workflow**

## GitHub Environments

For better security and deployment control, set up GitHub environments:

1. Go to your repository **Settings** > **Environments**
2. Create environments for `development` and `production`
3. Add environment-specific secrets
4. Configure protection rules:
   - **Required reviewers**: Require approval for production deployments
   - **Wait timer**: Add delay before deployment starts
   - **Deployment branches**: Limit which branches can deploy to production

## Deployment Strategy

### Development Workflow

1. Push changes to feature branch
2. Create pull request to `develop`
3. CI workflow validates changes
4. Merge to `develop`
5. Create beta release (e.g., `v1.0.0-beta.1`) 
6. Automatically deploys to development environment

### Production Workflow

1. Create pull request from `develop` to `main`
2. CI workflow validates changes
3. Review and merge to `main`
4. Create release (e.g., `v1.0.0`)
5. Automatically deploys to production environment

## Customizing Workflows

### Adding Custom Build Steps

Edit `.github/workflows/ci.yml` to add custom build steps.

For example, to add a custom linter:

```yaml
- name: Run custom linter
  run: |
    pip install your-linter
    your-linter --check .
```

### Adding Custom Deployment Steps

Edit `.github/workflows/deploy.yml` to add custom deployment steps.

For example, to add a notification:

```yaml
- name: Send deployment notification
  run: |
    curl -X POST https://your-notification-service.com/notify \
      -d "message=Deployment to ${{ github.event.inputs.environment }} completed"
```

## Monitoring Deployments

1. Check the **Actions** tab to see running and completed workflows
2. Review logs for each step in a workflow
3. View deployment outputs for connection details
4. For failed deployments, check:
   - GitHub Actions workflow logs
   - Terraform error messages
   - Server logs via SSH

## Rollback Process

If a deployment fails or introduces issues:

1. Return to the last successful release tag
2. Manually trigger the deploy workflow targeting that tag
3. Alternatively, SSH into the server and restart with the previous configuration

## Best Practices

- Use semantic versioning for releases (e.g., `v1.0.0`)
- Include detailed release notes describing changes
- Add environment-specific variables to appropriate GitHub environments
- Rotate secrets regularly (API keys, passwords, etc.)
- Use pre-releases (alpha/beta/rc) for testing before production releases

## Troubleshooting

### Failed CI Checks

- Check the specific test or lint error in the workflow logs
- Fix the issues locally and push again
- Verify tests pass locally before pushing

### Failed Deployments

- Check Terraform error messages in the workflow logs
- Verify that all required secrets are configured
- Ensure SSH key is valid and properly formatted
- Check cloud provider quotas and limits

### PyPI Publishing Issues

- Verify PyPI API token is correctly configured
- Ensure version in `pyproject.toml` is incremented
- Check that package name is available on PyPI