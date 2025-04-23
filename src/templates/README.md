# Documentation Templates

This directory contains Jinja2 templates for generating documentation. 

## Available Templates

- `architecture.md.j2` - Template for system architecture documentation

## Template Variables

### Architecture Template

- `title` - Title of the architecture document
- `description` - Overall description of the system architecture
- `components` - List of components in the system
  - `name` - Name of the component
  - `description` - Description of the component
  - `responsibilities` - List of component responsibilities
  - `interfaces` - List of component interfaces
- `relationships` - List of relationships between components
  - `source` - Source component
  - `target` - Target component
  - `description` - Description of the relationship
- `diagrams` - List of diagrams
  - `title` - Diagram title
  - `description` - Diagram description
  - `content` - Diagram content (e.g., ASCII art, mermaid.js code)
