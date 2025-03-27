# Insurance Management System

A comprehensive insurance management system tailored for the Nepal insurance market, providing end-to-end solutions for policy management, premium collection, claims processing, loan management, and regulatory compliance.

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technologies Used](#technologies-used)
- [Setup Instructions](#setup-instructions)
- [Module Descriptions](#module-descriptions)
  - [User Management](#user-management)
  - [Policy Management](#policy-management)
  - [Premium Management](#premium-management)
  - [Claims Management](#claims-management)
  - [Loan Management](#loan-management)
  - [Agent Management](#agent-management)
  - [Reporting System](#reporting-system)
  - [Surrender Process](#surrender-process)
- [Admin Guide](#admin-guide)
- [Nepal Regulatory Compliance](#nepal-regulatory-compliance)
- [Security Features](#security-features)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

The Insurance Management System is a Django-based application designed to streamline all operations of an insurance company in Nepal. It offers a comprehensive suite of features that handle the entire insurance lifecycle from policy issuance to claims settlement, with specific adaptations for Nepal's insurance regulations and business practices.

The system serves multiple stakeholders:
- **Insurance Company Administrators** - For managing operations, reporting, and compliance
- **Branch Managers** - For overseeing branch activities and performance
- **Underwriters** - For risk assessment and policy approval
- **Agents** - For policy sales and customer management
- **Policyholders** - For accessing policy details and making claims

## Key Features

- **Policy Administration**: Create, modify, and manage various insurance policy types with customizable terms
- **Premium Calculation & Collection**: Automated calculation of premiums with Nepal-specific tax compliance
- **Claims Processing**: End-to-end claims management with approval workflows
- **Agent Management**: Track agent performance, commissions, and licensing
- **Underwriting**: Risk assessment and premium loading based on policy risk factors
- **Loan Management**: Policy loans with interest calculation and repayment tracking
- **Surrender Processing**: Handle policy surrenders with GSV/SSV calculations
- **Reporting**: Comprehensive reporting for branches, agents, and policy performance
- **Regulatory Compliance**: Built-in features to comply with Beema Samiti (Insurance Board of Nepal) regulations
- **Bonus Calculation**: Automated bonus accrual for endowment policies

## System Architecture

The system follows a typical Django MVT (Model-View-Template) architecture:

- **Models**: Define database schema and business logic
- **Views**: Handle HTTP requests and implement controller logic
- **Templates**: Render HTML responses for both admin and frontend interfaces
- **Admin Interface**: Customized Django admin for complex insurance operations
- **Authentication**: Role-based access control for different user types
- **Database**: Uses Django ORM with PostgreSQL for robust data management

## Technologies Used

- **Backend**: Django 4.x
- **Database**: PostgreSQL 13+
- **Frontend**: HTML5, CSS3, JavaScript, jQuery, Bootstrap
- **Authentication**: Django Authentication System with custom extensions
- **Reporting**: Django templating system for PDF generation
- **Deployment**: Docker, Nginx, Gunicorn
- **Version Control**: Git
- **Scheduled Tasks**: Celery for automated calculations and notifications

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL 13+
- Virtualenv
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/insurance-management.git
   cd insurance-management
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a `.env` file with the following):
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://username:password@localhost:5432/insurance_db
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Start the development server:
   ```bash
   python manage.py runserver
   ```

8. Access the admin interface at `http://localhost:8000/admin/`

## Module Descriptions

### User Management

The system supports multiple user types, each with specific roles and permissions:

- **Superadmins**: Full system access
- **Company Admins**: Manage company-wide settings
- **Branch Admins**: Manage branch operations
- **Underwriters**: Evaluate and approve policies
- **Agents**: Create policy applications
- **Policyholders**: Access their policy information

The user management system includes:
- Role-based permissions
- Profile management
- OTP-based authentication for sensitive operations
- User activity tracking

### Policy Management

The core of the system revolves around policy management:

- **Policy Types**: Support for Term, Endowment, and other policy types
- **Policy Configuration**: Customizable policy parameters including:
  - Sum assured limits
  - Duration factors
  - Bonus rates
  - GSV/SSV rates
  - Accidental Death Benefit (ADB)
  - Permanent Total Disability (PTD)
- **Policy Lifecycle**: Manage policies from application to maturity
- **Underwriting Integration**: Risk assessment and approval workflows
- **Document Management**: Store policy documents, KYC documents, and more

### Premium Management

The premium management module handles all aspects of premium calculation and collection:

- **Premium Calculation**: Based on mortality rates, age, policy type, duration, and risk factors
- **Payment Scheduling**: Support for various payment frequencies (annual, semi-annual, quarterly)
- **Payment Tracking**: Monitor due dates, renewals, and pending payments
- **Late Payment Handling**: Automated fine calculation and grace period management
- **Nepal Tax Compliance**: VAT, service tax, and TDS calculations
- **Receipt Generation**: Printable receipts for all payments

### Claims Management

The claims module provides a complete workflow for processing insurance claims:

- **Claim Submission**: Record claim details including reason and documentation
- **Verification Process**: Multi-step approval workflow
- **Document Upload**: Attach supporting documents for claims
- **Benefit Calculation**: Automated calculation of claimable amount
- **Loan Adjustment**: Offset outstanding loans against claim amounts
- **Payment Processing**: Track status of claim payments
- **Printable Claim Forms**: Generate claim-related documentation

### Loan Management

The loan module allows policyholders to obtain loans against their policies:

- **Loan Eligibility**: Calculate maximum loan amounts based on GSV
- **Interest Calculation**: Daily interest accrual
- **Repayment Tracking**: Record and manage loan repayments
- **Outstanding Balance**: Real-time calculation of remaining loan amounts
- **Loan Types**: Support for different loan purposes
- **Loan Documents**: Generate loan agreements and repayment schedules
- **Integration with Claims**: Automatic adjustment of loans against claims or surrenders

### Agent Management

The agent management module handles all aspects of insurance agents:

- **Agent Applications**: Process new agent applications
- **Licensing**: Track license details, expiry dates, and renewals
- **Performance Tracking**: Monitor policy sales and renewals
- **Commission Calculation**: Automated commission processing based on policies sold
- **Reporting**: Generate performance reports for individual agents
- **Agent Hierarchy**: Support for team structures and hierarchical commissions
- **Document Management**: Store agent documents including licenses and training certificates

### Reporting System

The reporting system provides insights into all aspects of the insurance business:

- **Branch Reports**: Complete branch performance metrics
- **Agent Reports**: Individual and team agent performance
- **Policy Reports**: Active policy statistics and renewals
- **Financial Reports**: Premium collection, claim settlements, and financial health
- **Regulatory Reports**: Reports required by Beema Samiti (Nepal Insurance Board)
- **Custom Reports**: Generate reports for specific date ranges or parameters
- **Export Options**: Export reports to PDF or Excel formats

### Surrender Process

The surrender process module handles policy surrenders in various scenarios:

- **Voluntary Surrender**: Process policyholder-initiated surrenders
- **Automatic Surrender**: Handle surrenders due to non-payment
- **Maturity Surrender**: Process policies reaching their maturity date
- **Surrender Value Calculation**: Calculate GSV and SSV based on policy terms
- **Tax Handling**: Apply appropriate tax deductions (TDS) on surrender amounts
- **Loan Adjustment**: Deduct outstanding loans from surrender values
- **Documentation**: Generate surrender certificates and payment notifications
- **Workflow**: Multi-step approval process for surrender requests

## Admin Guide

The system is primarily administered through a customized Django admin interface:

### Main Admin Sections

1. **Dashboard**: Overview of system statistics and urgent actions
2. **Company Management**: Manage company and branch information
3. **User Management**: Create and edit various user types
4. **Policy Administration**: Configure and manage insurance policies
5. **Policyholder Management**: View and manage policyholders
6. **Premium Management**: Track premium payments and schedules
7. **Claims Processing**: Handle the claims workflow
8. **Loan Administration**: Approve and manage policy loans
9. **Agent Management**: Oversee agents and their performance
10. **Surrender Management**: Process policy surrenders
11. **Reporting**: Generate and export system reports

### Common Admin Tasks

- **User Creation**: Set up new staff members with appropriate permissions
- **Policy Configuration**: Define policy parameters and rates
- **Approval Workflows**: Process underwriting, claims, and surrender approvals
- **Report Generation**: Create periodic branch and agent reports
- **Backup Management**: Schedule and maintain data backups

## Nepal Regulatory Compliance

The system includes features specifically designed for Nepal's insurance regulations:

- **Beema Samiti Compliance**: Registration number tracking and reporting
- **KYC/AML Integration**: Know Your Customer and Anti-Money Laundering features
- **Tax Compliance**: Automated VAT, service tax, and TDS calculations
- **Statutory Reporting**: Generate reports required by Nepalese regulations
- **Document Requirements**: Nepal-specific document collection and verification
- **Policy Terms**: Standardized policy wording aligned with Nepal regulations
- **Financial Limits**: Adherence to regulatory limits for various operations

## Security Features

- **Role-Based Access Control**: Granular permissions for different user types
- **OTP Authentication**: Two-factor authentication for sensitive operations
- **Audit Trails**: Track all significant actions within the system
- **Data Encryption**: Secure storage of sensitive information
- **Session Management**: Secure session handling and timeout controls
- **Password Policies**: Enforce strong password requirements
- **Backup and Recovery**: Regular automated backups with secure storage

## Contributing

Contributions to the Insurance Management System are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a Pull Request

# Insurance Management System - New Features

## Policy Renewal Process

The policy renewal process has been completely revamped with the following features:

1. **Automated Renewal Detection**: The system automatically identifies policies approaching maturity and creates renewal records.
2. **Structured Renewal Workflow**: A clear process for initiating, tracking, and completing policy renewals.
3. **Tiered Reminder System**: Three-level reminder system (first, second, final) to notify policyholders about upcoming renewals.
4. **Grace Period Management**: Automatic tracking of grace periods with expiration handling.
5. **User-friendly Interface**: Clear dashboard for managing renewals with action buttons for each step.

## Agent Commission Dashboard

A comprehensive dashboard for sales agents to track their performance:

1. **Visual Commission Tracking**: Interactive charts showing commission trends over time.
2. **Performance Metrics**: Key performance indicators including:
   - Policy sales metrics
   - Premium collection stats
   - Target achievement visualization
   - Customer retention rates
   - Renewal success rates
   - Average policy value

3. **Commission History**: Detailed records of all commissions with status tracking.
4. **Goal Setting & Tracking**: Visual representation of progress toward sales targets.

## Multi-language Support

The system now includes robust internationalization support:

1. **Full i18n Implementation**: All user-facing text is now translation-ready using Django's i18n framework.
2. **English and Nepali Languages**: Complete bilingual support focusing on Nepal's official languages.
3. **Language Switcher**: Easy-to-use language toggle on all key interfaces.
4. **Localized Formatting**: Proper formatting for dates, currencies, and numbers in both languages.

## Implementation Notes

### Technical Improvements

1. **Template Standardization**: All templates now follow the same structure and style guidelines.
2. **Responsive Design**: All new interfaces are fully responsive and work on mobile devices.
3. **Clean URL Structure**: Logical and RESTful URL patterns for new functionality.
4. **Performance Optimization**: Efficient database queries for dashboard metrics.

### Setup Requirements

To enable the new features:

1. Run migrations to add new model fields:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

2. Compile translation files:
   ```
   django-admin compilemessages
   ```

3. Configure automated tasks for renewal reminders (requires setting up a task scheduler):
   ```python
   # Example cron job (add to your scheduler)
   from app.models import PolicyRenewal
   
   def check_renewals():
       renewals_due = PolicyRenewal.objects.filter(status='Pending', is_first_reminder_sent=False)
       for renewal in renewals_due:
           renewal.send_reminder('first')
   ```

### Future Enhancements

1. **SMS Integration**: Add SMS notifications for renewal reminders.
2. **Email Template Customization**: Allow admin customization of email templates.
3. **Additional Performance Metrics**: Expand the agent dashboard with more KPIs.
4. **Expanded Language Support**: Framework in place to easily add more languages. 
## License

This project is licensed under the MIT License - see the LICENSE file for details. 