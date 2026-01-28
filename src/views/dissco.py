"""
DiSSCo Integration Views

This module provides web views for the DiSSCo integration features.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from views import templates

route = APIRouter(tags=["views"])


@route.get("/dissco/tracking", response_class=HTMLResponse)
def show_dissco_tracking(request: Request):
    """
    Display the DiSSCo sample tracking page.
    
    This page allows users to enter specimen identifiers and track them
    across the DiSSCo network of European natural science collections.
    """
    response_params = {
        "title": "DiSSCo Sample Tracking",
        "subtitle": "Track samples across European collections",
        "search_page": True,
        "wp_footer": True,
        "request": request,
    }
    return templates.TemplateResponse("dissco_tracking.jinja2", response_params)
