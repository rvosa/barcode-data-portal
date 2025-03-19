# Static

This directory contains static assets used by the BOLD Public Portal web application. These assets are served directly to the client browser without processing by the application server.

## Overview

The static folder is mounted as a static file server in the FastAPI application, making all its contents accessible via HTTP. This approach improves performance by bypassing application processing for unchanging assets and enables browser caching.

## Directory Structure

```
static/
├── css/            # CSS stylesheets for styling the application
├── font-awesome/   # Font Awesome icon library
├── fonts/          # Web fonts used throughout the application
├── img/            # Images for the application (banners, backgrounds, etc.)
├── js/             # JavaScript files for client-side functionality
├── wp-content/     # WordPress content assets (styles, images, etc.)
├── wp-includes/    # WordPress core assets and dependencies
└── wp-json/        # WordPress REST API response fixtures/schemas
```

## Contents

### css/

Contains Cascading Style Sheets (CSS) that define the visual presentation of the application:
- Page layouts
- Color schemes
- Typography
- Responsive design rules

### font-awesome/

Includes the Font Awesome icon library, which provides scalable vector icons that can be customized with CSS.

### fonts/

Contains web fonts used throughout the application for consistent typography across different platforms and browsers.

### img/

Stores images used in the application, including:
- Banner images for section headers
- Background images
- Logos
- UI elements and icons

### js/

Contains JavaScript files for client-side functionality:
- Data visualization (charts, maps)
- AJAX requests to the API services
- DOM manipulation
- Event handling
- Third-party library integrations

### WordPress Integration Folders

The application integrates WordPress assets through three key directories:

#### wp-content/

Contains WordPress theme-specific assets:
- Theme stylesheets
- Theme images
- Custom WordPress templates

#### wp-includes/

Contains WordPress core functionality assets:
- Core JavaScript files
- WordPress CSS
- Shared utilities

#### wp-json/

Contains WordPress REST API response fixtures or schemas. This may be used for:
- Local development without a live WordPress instance
- Documentation of API response structures
- Testing

## Integration with Overall Architecture

The static folder is integrated with the application in several ways:

1. **Mounted in FastAPI**: The folder is mounted in the FastAPI application's main.py:
   ```python
   app.mount("/static", StaticFiles(directory="static"), name="static")
   app.mount("/wp-content", StaticFiles(directory="static/wp-content"), name="wp-content")
   app.mount("/wp-includes", StaticFiles(directory="static/wp-includes"), name="wp-includes")
   app.mount("/wp-json", StaticFiles(directory="static/wp-json"), name="wp-json")
   ```

2. **Referenced in Templates**: Static assets are referenced in Jinja2 templates:
   ```html
   <link href="/static/css/style.css" rel="stylesheet">
   <script src="/static/js/main.js"></script>
   <img src="/static/img/banner.jpg" alt="Banner">
   ```

3. **WordPress Integration**: The WordPress-related folders enable the application to present a unified interface while leveraging WordPress for content management:
   - Templates include WordPress content
   - Styling is maintained consistently
   - WordPress functionality is available without a full WordPress installation

## Deployment Considerations

When deploying the application:
- Static assets should be served by a web server (like Nginx) where possible for improved performance
- Consider using a CDN for global distribution of static assets
- Implement proper caching headers for optimal browser caching
- Minify and bundle CSS and JavaScript files for production

## Related Components

- **templates/**: References static assets in the HTML templates
- **views/**: Controllers that render templates using static assets
- **services/**: API endpoints that may be called by JavaScript in the static folder