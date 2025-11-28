# Email Templates - White-Label Customization

This directory contains email templates for the 6-digit authentication token system.

## Template Files

- `token_email.txt` - Plain text email template for 6-digit tokens
- `token_email.html` - HTML email template for 6-digit tokens (future use)

**Git Tracking:** These templates are tracked in git as defaults. Custom white-label templates can be added per deployment.

## White-Label Customization

### For Development
The default templates work out of the box and use environment variables for basic customization.

### For Production Deployments

**Method 1: Environment Variables (Recommended)**

Customize via `backend/.env`:

```bash
APP_NAME=Your Company Name
COMPANY_NAME=Your Company
SUPPORT_EMAIL=support@yourcompany.com
BRAND_PRIMARY_COLOR=#007bff
```

**Method 2: Custom Templates**

1. Create custom template files in this directory
2. Copy and modify from defaults
3. Deploy via Docker volume mount or include in build

### Available Template Variables

Templates use Jinja2 syntax with these variables:

- `{{ token }}` - The 6-digit authentication code
- `{{ expiry_minutes }}` - Token expiration time (default: 15)
- `{{ app_name }}` - Application name (from APP_NAME env var)
- `{{ company_name }}` - Company name (from COMPANY_NAME env var)
- `{{ brand_color }}` - Primary brand color (from BRAND_PRIMARY_COLOR env var)
- `{{ support_email }}` - Support contact email (from SUPPORT_EMAIL env var)

### Example Custom Template

```text
Welcome to {{ app_name }}!

Your verification code is:

{{ token }}

This code will expire in {{ expiry_minutes }} minutes.

Need assistance? Contact us at {{ support_email }}

Best regards,
{{ company_name }}
```

## Fallback System

The `template_service.py` includes built-in fallback templates to ensure emails are always sent, even if template files are missing or corrupted.

## Testing Templates

```bash
# Start backend with your custom environment variables
docker-compose up backend

# Trigger token request to test email rendering
curl -X POST http://localhost:8000/api/v1/auth/request-token \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## Best Practices

1. **Keep it simple** - Plain text is more reliable than HTML for authentication emails
2. **Test thoroughly** - Verify templates across different email clients
3. **Use environment variables** - Avoid hardcoding company-specific details
4. **Version control** - Consider tracking custom templates in your deployment repo
