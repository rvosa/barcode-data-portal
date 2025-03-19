# BOLD Public Portal

This repository contains the codebase for the BOLD (Barcode of Life Data) Public Portal, a web application that provides access to biodiversity data through a REST API and web interface.

## Project Structure

```
src/
├── main.py                  # FastAPI application entry point
├── dao.py                   # Data Access Object for Couchbase operations
├── settings.py              # Application configuration settings
├── util.py                  # Utility functions for the application
├── logging.ini              # Logging configuration for main application
├── socketserver_logging.py  # Socket server for centralized logging
├── socketserver_logging.ini # Logging configuration for socket server
├── cypress/                 # End-to-end testing with Cypress
├── ETL/                     # Extract, Transform, Load scripts for data processing
├── services/                # API services and business logic
├── static/                  # Static files (CSS, JavaScript, images)
├── templates/               # Jinja2 HTML templates
├── tools/                   # Utility scripts and tools
└── views/                   # Web view controllers
```

## Core Components

### Main Application Files

- **main.py**: FastAPI application entry point that defines routes, middleware, and exception handlers.
- **dao.py**: Data Access Object that handles interactions with the Couchbase database.
- **settings.py**: Configuration settings for the application using Pydantic.
- **util.py**: Utility functions for triplet handling, caching, and security.

### Configuration and Logging

- **logging.ini**: Logging configuration that sends logs to a socket server.
- **socketserver_logging.py**: Socket server implementation for centralized logging.
- **socketserver_logging.ini**: Configuration for the logging socket server that writes to log files.

### Directories

- **cypress/**: Contains end-to-end tests using Cypress framework.
- **ETL/**: Contains scripts for extracting, transforming, and loading data into the system.
- **services/**: API service implementations organized by functionality:
  - query: Search functionality
  - summary: Data summarization
  - taxonomy: Taxonomic data operations
  - documents: Document retrieval
  - terms: Term management
  - stats: Statistical data
  - and others

- **static/**: Static web assets including CSS, JavaScript, and images.
- **templates/**: Jinja2 HTML templates for rendering web pages.
- **tools/**: Utility scripts and tools for development and maintenance.
- **views/**: Web view controllers for different sections of the portal:
  - index: Homepage
  - record: Individual record display
  - recordset: Dataset views
  - country: Country-specific views
  - and others

## Architecture

The BOLD Public Portal uses a modern web architecture with:

- **FastAPI**: High-performance web framework for building APIs
- **Couchbase**: NoSQL database for data storage
- **Redis**: In-memory data structure store used for caching
- **Jinja2**: Template engine for HTML rendering

The application follows a layered architecture:
1. **Web Layer**: Views and templates
2. **API Layer**: RESTful services
3. **Business Logic Layer**: Service implementations
4. **Data Access Layer**: DAO components for database operations

## Development

### Prerequisites

- Python 3.8+
- Couchbase
- Redis
- Node.js (for Cypress testing)

### Environment Setup

The application uses environment variables for configuration, which can be set in the settings.py file or through environment variables.

### Running the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Logging

The application uses a centralized logging system with:
- Socket-based logging for application components
- File-based logging for persistent storage
- Separate log files for exceptions, security events, access logs, and database queries

## API Documentation

When running, API documentation is available at `/api/docs` (Swagger UI) and `/api/redoc` (ReDoc).