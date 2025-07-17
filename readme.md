# Professional Invoice Management System

## Overview

This is a Flask-based invoice management system designed to provide professional invoice generation and management capabilities. The application features a modern web interface with a purple gradient theme, database persistence using SQLAlchemy, and comprehensive invoice tracking functionality.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: SQLite for development (configurable to PostgreSQL via DATABASE_URL environment variable)
- **Models**: Company, Client, Invoice, and LineItem entities with proper relationships
- **Session Management**: Flask sessions with configurable secret key
- **Deployment**: WSGI-ready with ProxyFix middleware for production deployment

### Frontend Architecture
- **Template Engine**: Jinja2 templating with base template inheritance
- **CSS Framework**: Bootstrap 5 with custom CSS styling
- **UI Theme**: Purple gradient design (#4f46e5 → #7c3aed) with smooth animations
- **Icons**: Font Awesome integration
- **JavaScript**: Vanilla JS for dynamic functionality and form interactions
- **PDF Generation**: html2pdf.js library for invoice PDF export

### Database Schema
The system uses a relational database with the following key entities:
- **Company**: Stores business information (name, address, contact details, tax ID)
- **Client**: Customer information with contact details
- **Invoice**: Core invoice data with financial calculations and status tracking
- **LineItem**: Individual invoice line items (implied from routes but not fully shown in models.py)

## Key Components

### Core Pages
1. **Create Invoice** (`/create-invoice`): Dynamic invoice creation with live preview
2. **Company Settings** (`/company-settings`): Business profile management
3. **Invoice History** (`/invoice-history`): Invoice tracking with search and filtering

### Data Management
- **Invoice Numbering**: Unique invoice number generation
- **Status Tracking**: Pending, Paid, Overdue status management
- **Financial Calculations**: Automatic subtotal, tax, and total calculations
- **Date Management**: Issue date and due date tracking

### User Interface Features
- **Responsive Design**: Mobile-friendly layout using Bootstrap grid system
- **Animation Effects**: Slide-in animations and hover effects
- **Interactive Elements**: Dynamic form fields and real-time calculations
- **Search & Filter**: Invoice history filtering by status and search terms
- **Statistics Dashboard**: Revenue and invoice count summaries

## Data Flow

1. **Invoice Creation Flow**:
   - User selects/creates company information
   - Enters client details
   - Adds line items with automatic calculation updates
   - Generates PDF for download or email

2. **Data Persistence**:
   - Form data auto-saves to localStorage for user experience
   - Database persistence through SQLAlchemy ORM
   - Relationship mapping between companies, clients, and invoices

3. **Invoice Management**:
   - Status updates trigger recalculation of statistics
   - Search functionality queries across invoice numbers and client names
   - Historical data provides business insights

## External Dependencies

### Python Libraries
- **Flask**: Web framework and routing
- **Flask-SQLAlchemy**: Database ORM and management
- **Werkzeug**: WSGI utilities and proxy handling

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI elements
- **html2pdf.js**: Client-side PDF generation

### Development Tools
- **SQLite**: Default database for development
- **Logging**: Built-in Python logging for debugging

## Deployment Strategy

### Environment Configuration
- **Database**: Configurable via DATABASE_URL environment variable
- **Security**: Session secret via SESSION_SECRET environment variable
- **Connection Pooling**: SQLAlchemy engine optimization for production

### Production Considerations
- **WSGI Deployment**: Ready for deployment with ProxyFix middleware
- **Database Migration**: Automatic table creation on startup
- **Static Assets**: Organized static file structure for CDN deployment
- **Error Handling**: Comprehensive logging and error management

### Scalability Features
- **Database Agnostic**: Easy migration from SQLite to PostgreSQL
- **Session Management**: Stateless design for horizontal scaling
- **Asset Optimization**: Modular CSS and JavaScript for performance

The application follows a traditional MVC pattern with clear separation of concerns, making it maintainable and extensible for additional features like payment integration, email notifications, or multi-tenant support.
