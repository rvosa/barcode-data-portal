# Views

This directory contains the view controllers for the BOLD Public Portal web application. The view controllers handle HTTP requests and render HTML responses using Jinja2 templates.

## Overview

The view controllers follow a similar pattern:
- They define FastAPI routes for specific URL paths
- They gather data from the API services
- They render Jinja2 templates with the collected data

The `__init__.py` file provides shared functionality for all views, including the Jinja2 template engine setup and utility functions for date histogram generation.

## Files

- `__init__.py`: Sets up the Jinja2 template engine and provides utility functions for date histogram generation
- `about.py`: Renders the about page
- `api.py`: Renders the API documentation page
- `bin.py`: Handles BIN (Barcode Index Number) views, including home and individual BIN pages
- `country.py`: Handles country/ocean views, including home and individual country pages
- `index.py`: Renders the application's homepage
- `inst.py`: Handles institution views, including home and individual institution pages
- `lookup.py`: Provides a simple lookup service
- `primer.py`: Renders the primer home page
- `record.py`: Handles individual record views
- `recordset.py`: Handles dataset views, including home and individual dataset pages
- `result.py`: Renders search results
- `sequence.py`: Handles sequence viewing
- `theme.py`: Renders the theme demonstration page

## Key Components

### Jinja2 Templates

Templates are initialized in `__init__.py` and shared across all views:

```python
templates = Jinja2Templates(directory="templates")
```

### Route Patterns

Most view controllers follow this pattern:

```python
@route.get("/<path>", response_class=HTMLResponse)
async def show_view(request: Request, ...):
    # Collect data from API services
    
    # Prepare response parameters
    response_params = {
        "title": "Title",
        "subtitle": "Subtitle",
        # ... other parameters
        "request": request,  # Required by Jinja2Templates
    }
    
    # Render template
    return templates.TemplateResponse("template.jinja2", response_params)
```

### Data Collection

Views typically gather data using the httpx client to make requests to the API services:

```python
async with httpx.AsyncClient(timeout=None) as client:
    # Make API requests to get data
    resp = await client.get(url=f"{get_app_url()}/api/summary", params=params)
    # ... process response
```

### Error Handling

Views implement consistent error handling for API requests:

```python
try:
    # API requests
except httpx.HTTPStatusError:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Page failed to load, please try again",
    )
```

## Utility Functions

The `__init__.py` file provides utility functions for generating date histograms:

- `generate_date_histogram`: Creates a histogram of dates from count data
- `generate_cumulative_date_histogram`: Creates a cumulative histogram of dates

## Integration with Overall Architecture

The views layer:

1. **Consumes from**:
   - FastAPI routing system
   - API services (via internal HTTP requests)
   - Jinja2 template engine

2. **Produces**:
   - HTML responses for end users

Views never directly access the database; they always go through the API services layer to maintain separation of concerns. This enables:
- Clean separation between presentation and business logic
- Ability to change the presentation without affecting the underlying API
- Reuse of API endpoints for both web and programmatic access

## Related Directories

- `templates/`: Contains the Jinja2 templates rendered by these views
- `services/`: Contains the API services that provide data to the views
- `static/`: Contains static assets (CSS, JavaScript, images) used by the templates