# Cypress

This directory contains end-to-end testing infrastructure for the BOLD Public Portal using the Cypress testing framework. These tests validate the functionality of both the web interface and API services.

## Overview

The Cypress tests ensure that the BOLD Public Portal functions correctly from the user's perspective by automating browser interactions and API calls. These tests verify that:

1. Web pages render correctly
2. User interactions work as expected
3. API endpoints return proper responses
4. Data flows correctly through the system

## Directory Structure

```
cypress/
├── user_journey/          # End-to-end user flow tests
├── plugins/               # Cypress plugins configuration
├── support/               # Support files and custom commands
├── templates/             # Template files for creating new tests
├── e2e/                   # End-to-end tests organized by component type
│   ├── views/             # Tests for web view controllers
│   └── services/          # Tests for API services
└── cypress.config.js      # Cypress configuration file
```

## Test Categories

### User Journey Tests

Located in `user_journey/`, these tests simulate complete user workflows across multiple pages, validating that common user tasks can be completed successfully:

- `fungal.cy.js`: Tests searching and browsing fungal data
- `brazil.cy.js`: Tests geographic data filtering for Brazil
- `search.cy.js`: Tests the search functionality

### View Tests

Located in `e2e/views/`, these tests focus on individual web pages:

- Tests for each page type (index, record, recordset, country, etc.)
- Validates page rendering, UI elements, and client-side functionality
- Ensures correct display of data from the backend

### Service Tests

Located in `e2e/services/`, these tests validate the API services:

- Tests for each service endpoint (query, summary, documents, etc.)
- Validates request handling, response formats, and error conditions
- Ensures data consistency and correctness

### Template Tests

Located in `templates/`, these are boilerplate files to help create new tests:

- `serviceTemplate.cy.js`: Template for new service tests
- `viewTemplate.cy.js`: Template for new view tests
- `userJourneySample.cy.js`: Template for new user journey tests
- `subcall.cy.js`: Template for creating test components

## Support Files

Located in `support/`:

- `commands.js`: Custom Cypress commands specific to the BOLD Portal
- `index.js`: Main support file imported in all test files
- `e2e.js`: Configuration for end-to-end tests

## Integration with Overall Architecture

The Cypress tests interact with the BOLD Public Portal in several ways:

1. **Web Interface Testing**: Tests interact with the HTML/CSS/JavaScript rendered by the templates and views
2. **API Testing**: Tests make requests to API endpoints implemented in the services directory
3. **Data Validation**: Tests verify that data from the Couchbase database (via DAO) is correctly displayed
4. **Regression Prevention**: Tests ensure that new changes don't break existing functionality

## Running the Tests

Tests can be run using the Cypress test runner:

```bash
# Open the Cypress test runner
npx cypress open

# Run all tests headlessly
npx cypress run

# Run a specific test file
npx cypress run --spec "cypress/e2e/views/index.cy.js"

# Run tests for a specific category
npx cypress run --spec "cypress/e2e/services/**"
```

## Related Components

- **views/**: The web controllers being tested by the view tests
- **services/**: The API endpoints being tested by the service tests
- **templates/**: The Jinja2 templates that generate the HTML being tested
- **static/**: The frontend assets (CSS, JavaScript) that implement the client-side functionality being tested

## Test Development Guidelines

When adding new functionality to the BOLD Public Portal:

1. Add corresponding Cypress tests to validate the new feature
2. Use the templates in the `templates/` directory as a starting point
3. For UI components, add tests in the `e2e/views/` directory
4. For API endpoints, add tests in the `e2e/services/` directory
5. For complex user workflows, add tests in the `user_journey/` directory