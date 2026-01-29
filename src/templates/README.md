# Templates

This directory contains the Jinja2 templates used by the BOLD Public Portal web application. These templates define the HTML structure and presentation of the various pages in the application.

## Overview

The templates follow a hierarchical structure:
1. Base templates that define the overall HTML structure
2. Page-specific templates that extend the base templates
3. Reusable components/includes that can be incorporated into multiple pages
4. WordPress integration templates (wp-templates) for content management

Templates are rendered by the view controllers in the `views/` directory, which provide the data context for template rendering.

## Directory Structure

```
templates/
├── includes/           # Reusable components and the base template
│   ├── base.jinja2     # Main base template with common structure
│   ├── ancillary_data.jinja2
│   ├── ancillary_table.jinja2
│   ├── bin_searchbar.jinja2
│   ├── coordinates_map.jinja2
│   ├── footer.jinja2
│   ├── image_gallery.jinja2
│   ├── navbar.jinja2
│   ├── records_table.jinja2
│   ├── searchbar.jinja2
│   └── taxon_treemap.jinja2
│
├── wp-templates/       # WordPress content templates
│   ├── about.html
│   ├── api.html
│   ├── bin_home.html
│   ├── country_home.html
│   ├── index.html
│   ├── inst_home.html
│   ├── offline.html
│   ├── primer_home.html
│   ├── recordset_home.html
│   ├── sequence.html
│   └── theme.html
│
├── about.jinja2        # Page templates for various sections
├── api.jinja2
├── bin.jinja2
├── bin_home.jinja2
├── country.jinja2
├── country_home.jinja2
├── index.jinja2
├── inst.jinja2
├── inst_home.jinja2
├── offline.jinja2
├── primer_home.jinja2
├── record.jinja2
├── recordset.jinja2
├── recordset_home.jinja2
├── result.jinja2
├── sequence.jinja2
└── theme.jinja2
```

## Main Template Files

These Jinja2 templates define the specific pages of the application:

- **about.jinja2**: About page template
- **api.jinja2**: API documentation page template
- **bin.jinja2**: Individual BIN (Barcode Index Number) view template
- **bin_home.jinja2**: BIN home/landing page template
- **country.jinja2**: Individual country/ocean view template
- **country_home.jinja2**: Countries home/landing page template
- **index.jinja2**: Homepage template
- **inst.jinja2**: Individual institution view template
- **inst_home.jinja2**: Institutions home/landing page template
- **offline.jinja2**: Offline notice page template
- **primer_home.jinja2**: Primers home/landing page template
- **record.jinja2**: Individual record view template
- **recordset.jinja2**: Individual dataset view template
- **recordset_home.jinja2**: Datasets home/landing page template
- **result.jinja2**: Search results page template
- **sequence.jinja2**: Sequence view template
- **theme.jinja2**: Theme demonstration page template

## Includes Folder

The `includes/` directory contains reusable components and the base template:

- **base.jinja2**: The main layout template that all page templates extend
- **ancillary_data.jinja2**: Template for displaying ancillary data
- **ancillary_table.jinja2**: Template for data tables of ancillary information
- **bin_searchbar.jinja2**: Search bar for BINs
- **coordinates_map.jinja2**: Template for displaying geographical maps
- **image_gallery.jinja2**: Template for image galleries
- **records_table.jinja2**: Template for data tables of records
- **searchbar.jinja2**: Main search bar component
- **taxon_treemap.jinja2**: Template for taxonomy tree maps

These components are included in the main page templates as needed to provide consistent UI elements across the application.

## WP-Templates Folder

The `wp-templates/` directory contains HTML templates that are used to integrate WordPress content. These templates are included in the main Jinja2 templates using the `{% include %}` directive.

This approach allows for:
1. Content management through WordPress for non-technical users
2. Separation of dynamic application content from static/CMS content
3. Easy updates to content without modifying application code

## Template Structure Pattern

Most templates follow this pattern:
1. Extend the base template (`{% extends "includes/base.jinja2" %}`)
2. Define a title block (`{% block title %}{% endblock %}`)
3. Define a head block for CSS and JavaScript (`{% block head %}{% endblock %}`)
4. Define the main content block (`{% block content %}{% endblock %}`)
5. Include WordPress content templates as needed (`{% include "wp-templates/page.html" %}`)

## JavaScript Integration

Templates often include JavaScript that:
- Initializes UI components
- Makes AJAX calls to the API services
- Creates visualizations using libraries like Chart.js
- Manipulates the DOM based on user interactions

## Integration with Overall Architecture

The templates layer:

1. **Consumes from**:
   - View controllers (`views/` directory) that render templates with data
   - API services (via JavaScript AJAX calls) for dynamic data loading
   - Static assets (CSS, JavaScript, images) for styling and functionality
   - WordPress content (via wp-templates) for CMS-managed content

2. **Produces**:
   - HTML responses for end users
   - Client-side JavaScript for UI interactivity

## Template Rendering Process

1. User requests a page (e.g., `/recordset/DS-EXAMPLE`)
2. The FastAPI router directs the request to the appropriate view controller
3. The view controller collects the necessary data from services
4. The view controller renders the template with the collected data
5. The rendered HTML is sent back to the user's browser
6. Client-side JavaScript in the template may make additional API calls to load data

## Related Components

- **views/**: View controllers that render templates with data context
- **services/**: API endpoints that provide data to templates via AJAX
- **static/**: Static assets (CSS, JavaScript, images) referenced by templates