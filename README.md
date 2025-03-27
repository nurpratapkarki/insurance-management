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
- [Access Guide](#access-guide)
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
- **System Protection**: Automatic freeze of surrendered policies to prevent premium payments, loans, or renewals
- **Certificate Printing**: Generate and print surrender certificates

#### Recent Updates to Surrender Process
- Enhanced surrender certificate printing with automatic print dialog
- Added protection against operations on surrendered policies
- Improved validation for surrender status changes
- Added support for processing surrenders that are already in "Processed" status
- Implemented signal-based system to ensure consistent surrender status across the system

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

- **User Creation**: Set up new staff accounts with appropriate roles
- **Policy Configuration**: Create and manage policy products
- **Approval Workflows**: Handle policy, claim, and loan approvals
- **Financial Review**: Monitor premium collections and claims payouts
- **Reporting**: Generate period-end reports for business analysis
- **Compliance**: Ensure adherence to Nepal insurance regulations

## Access Guide

### How to Access System Screens

All main modules are accessible through the Django admin interface at `/admin/`. Here's how to navigate to each section:

#### Policy Management
- **Access Path**: Admin > App > Policy Holders
- **URL**: `/admin/app/policyholder/`
- **Features**: Create, view, edit policies; policy approval; document management

#### Premium Management
- **Access Path**: Admin > App > Premium Payments
- **URL**: `/admin/app/premiumpayment/`
- **Features**: Record payments; view payment history; generate receipts

#### Claims Management
- **Access Path**: Admin > App > Claim Requests
- **URL**: `/admin/app/claimrequest/`
- **Features**: Create new claims; view/process existing claims; upload claim documents

#### Loan Management
- **Access Path**: Admin > App > Loans
- **URL**: `/admin/app/loan/`
- **Features**: Create new loans; manage repayments; view loan history

#### Surrender Management
- **Access Path**: Admin > App > Policy Surrenders
- **URL**: `/admin/app/policysurrender/`
- **Features**: 
  - Create/view surrenders at `/admin/app/policysurrender/`
  - Process a specific surrender at `/admin/app/policysurrender/<id>/change/`
  - Print surrender certificate at `/admin/print-surrender-certificate/<id>/`
  - Access surrender process via buttons in the changelist view
  - Surrender approval and payment processing through status changes

#### Agent Management
- **Access Path**: Admin > App > Sales Agents
- **URL**: `/admin/app/salesagent/`
- **Features**: Manage agents; track performance; calculate commissions

#### Policy Renewal
- **Access Path**: Admin > App > Policy Renewals
- **URL**: `/admin/app/policyrenewal/`
- **Features**: View pending renewals; process renewals; send reminders

#### User Management
- **Access Path**: Admin > Authentication and Authorization > Users
- **URL**: `/admin/auth/user/`
- **Features**: Manage system users and their permissions

#### Reports
- **Access Path**: Admin > App > Reports (or specific report types)
- **URL**: Various report-specific URLs
- **Features**: Generate and export reports for different aspects of the business

### Special Feature Access

- **Print Surrender Certificate**: Available as a button on surrender detail page or list view (for Approved/Processed surrenders)
- **Policy Renewal**: Access renewal buttons from the Policy Renewal list page
- **Claim Payment Processing**: Buttons available in Claims Processing view
- **Agent Commission**: Accessible from agent detail page or commission list

## Nepal Regulatory Compliance

The system is designed to comply with Nepal's insurance regulations:

- **Beema Samiti Guidelines**: Adheres to rules set by Nepal's Insurance Board
- **Documentation**: Generates all required regulatory documents
- **Reporting**: Supports required regulatory reports
- **Tax Handling**: Calculates and tracks Nepal-specific taxes:
  - VAT (13%)
  - Insurance Service Tax
  - TDS on surrender and maturity
- **Policy Terms**: Configurable to match Nepal insurance product requirements

## Security Features

The system implements several security features:

- **Role-Based Access**: Users can only access permitted modules
- **Audit Logging**: Tracks all sensitive operations
- **OTP Authentication**: Required for high-risk actions
- **Data Encryption**: Sensitive data is encrypted at rest
- **Session Management**: Security settings for session timeouts
- **Backup Systems**: Regular automated database backups

## Contributing

Please refer to CONTRIBUTING.md for guidelines on how to contribute to this project.

## License

This project is licensed under the [LICENSE NAME] - see the LICENSE file for details. 