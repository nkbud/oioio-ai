# How to Use the API Frontend

This guide explains how to use and customize the HTMX-based frontend for the OIOIO MCP Agent.

## Overview

The frontend provides a user-friendly interface for interacting with the OIOIO MCP Agent system. It's built using:

- **HTMX** for interactive UI without complex JavaScript
- **Tailwind CSS** for responsive styling
- **Alpine.js** for minimal client-side interactions
- **Jinja2 Templates** for server-side rendering

## Accessing the Frontend

The frontend is served by the API server at the root URL. To access it:

1. Start the API server:
   ```bash
   python -m oioio_mcp_agent serve
   ```

2. Visit http://localhost:8000/ in your web browser

## Authentication

The frontend supports both password-based authentication and OAuth:

1. Navigate to http://localhost:8000/login
2. Enter your email and password, or click "Sign in with Google"

## Pages and Features

### Home Page
- Overview of the system
- Quick links to login and documentation

### Dashboard
- System status overview
- Agent activity monitoring
- Recent knowledge files
- System logs

### Agents
- List and manage agents
- Start and stop agents
- View agent logs and status
- Configure agent parameters

### Knowledge
- Browse and search knowledge files
- View file contents
- Upload new knowledge files
- Edit file metadata and tags

### Settings
- User profile management
- Tenant configuration
- System settings

## Customizing the Frontend

### Template Structure

```
oioio_mcp_agent/api/templates/
├── layouts/
│   └── base.html       # Base template with common structure
├── components/
│   ├── navbar.html     # Navigation bar
│   └── ...             # Other reusable components
└── pages/
    ├── index.html      # Home page
    ├── login.html      # Login page
    ├── dashboard.html  # Dashboard page
    └── ...             # Other page templates
```

### Customizing Templates

To customize the templates:

1. Copy the default templates from the package to your project:
   ```bash
   cp -r $(python -c "import oioio_mcp_agent; print(oioio_mcp_agent.__path__[0])")/api/templates ./custom_templates
   ```

2. Modify the templates as needed

3. Set the templates directory in your config.yaml:
   ```yaml
   api:
     templates_dir: "/path/to/your/custom_templates"
   ```

### Adding Custom CSS or JavaScript

To add custom styles or scripts:

1. Create a directory for static files:
   ```bash
   mkdir -p static/{css,js}
   ```

2. Add your custom files to these directories

3. Configure the static files directory in your config.yaml:
   ```yaml
   api:
     static_dir: "/path/to/your/static"
   ```

4. Reference your custom files in the templates:
   ```html
   <link rel="stylesheet" href="/static/css/custom.css">
   <script src="/static/js/custom.js"></script>
   ```

## Integration with OAuth

To enable Google OAuth login:

1. Create a Google OAuth application in the Google Developer Console
2. Add the redirect URI: `http://your-domain.com/api/auth/callback/google`
3. Set the client ID and secret in your environment or .env file:

```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

## Multi-Tenant Support

The UI automatically adapts to the current user's tenant:

- Regular users see only their tenant's resources
- Tenant admins see management options for their tenant
- System admins see all tenants and system-wide settings

## Next Steps

- Learn about [API Backend Integration](./api_backend.md)
- Set up [Cloud Deployment](../deployment/terraform.md)
- Explore [Custom Plugin Development](./custom_plugins.md)