# Insurance Management System for Nepal

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Django](https://img.shields.io/badge/django-4.x-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-13+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

**A comprehensive Django-based solution for insurance companies in Nepal**

</div>

## 📋 Overview

The Insurance Management System is a robust, enterprise-grade application designed specifically for the Nepali insurance market. It streamlines the entire insurance lifecycle from policy creation to claims settlement, surrender processing, and regulatory compliance.

### ✨ Key Features

- **Policy Administration** - Create and manage diverse policy types with customizable parameters
- **Premium Management** - Automated calculation with Nepal-specific tax compliance
- **Claims Processing** - Complete workflow from submission to settlement
- **Agent Network** - Commission tracking, licensing, and performance analytics
- **Loan Management** - Policy loans with interest calculation
- **Surrender Processing** - GSV/SSV calculations with certificate generation
- **Regulatory Compliance** - Built-in features for Beema Samiti requirements
- **Comprehensive Reporting** - Business intelligence across all operations

## 🏗️ Architecture

The system follows Django's MVT (Model-View-Template) architecture with:

- **Role-based access control** for different stakeholder types
- **Customized Django admin** for insurance-specific operations
- **PostgreSQL database** for robust data integrity
- **Responsive frontend** for both staff and policyholder access

## 🛠️ Tech Stack

- **Backend**: Django 4.x
- **Database**: PostgreSQL 13+
- **Frontend**: HTML5, CSS3, JavaScript, jQuery, Bootstrap
- **Deployment**: Docker, Nginx, Gunicorn
- **Task Scheduling**: Celery for automated calculations
- **Reporting**: Dynamic PDF generation

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 13+
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/nurpratapkarki/insurance-management.git
cd insurance-management

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (create .env file)
echo "DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://username:password@localhost:5432/insurance_db" > .env

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Launch server
python manage.py runserver
```

Visit `http://localhost:8000/admin/` to access the system.

## 📊 Core Modules

### 👥 User Management

Multi-level user hierarchy with specialized roles:
- **Superadmins** - Complete system access
- **Company Admins** - Organization-wide management
- **Branch Admins** - Branch-specific operations
- **Underwriters** - Risk assessment and approvals
- **Agents** - Policy sales and customer management
- **Policyholders** - Self-service portal

### 📝 Policy Management

Configure and manage all aspects of insurance policies:
- Multiple policy types (Term, Endowment, etc.)
- Customizable policy parameters
- Document management
- Underwriting workflows
- Policy lifecycle tracking

### 💰 Premium Management

Comprehensive premium handling:
- Risk-based calculation engine
- Multiple payment frequencies
- Late payment processing
- Nepal tax compliance (VAT, service tax)
- Receipt generation

### ⚠️ Claims Processing

End-to-end claims workflow:
- Multi-stage verification
- Document management
- Benefit calculation
- Loan adjustment
- Payment tracking

### 💸 Loan Management

Policy-secured loan processing:
- Eligibility calculation
- Interest accrual
- Repayment tracking
- Integration with claims/surrender

### 🤝 Agent Management

Complete agent lifecycle:
- Licensing and credentials
- Performance tracking
- Commission calculation
- Hierarchical structures
- Document storage

### 📈 Reporting System

Business intelligence across operations:
- Branch performance
- Agent productivity
- Financial insights
- Regulatory compliance reports
- Customizable reporting

### 📄 Surrender Processing

Handle policy surrenders:
- Calculation of surrender values
- Loan adjustment
- Documentation
- Certificate generation
- Multi-step approval workflow

## 👩‍💼 Admin Guide

### Main Administrative Sections

1. **Dashboard** - `/admin/`
2. **Policy Management** - `/admin/app/policyholder/`
3. **Premium Management** - `/admin/app/premiumpayment/`
4. **Claims Management** - `/admin/app/claimrequest/`
5. **Loan Management** - `/admin/app/loan/`
6. **Surrender Management** - `/admin/app/policysurrender/`
7. **Agent Management** - `/admin/app/salesagent/`
8. **Reporting** - Various report-specific URLs

### Special Features

- **Surrender Certificate Printing** - Available from surrender detail page
- **Policy Renewal** - Access via renewal list page
- **OTP Authentication** - For sensitive operations
- **Audit Logging** - Tracks all system activities

## 🔐 Security Features

- Role-based access control
- Data encryption for sensitive information
- Session management
- Comprehensive audit logging
- Automated backups

## 📜 Regulatory Compliance

Designed specifically for Nepal's insurance market:
- Beema Samiti (Insurance Board) compliance
- Nepal-specific tax handling (VAT, service tax, TDS)
- Required regulatory documentation
- Statutory reporting

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
Developed by <a href="https://github.com/nurpratapkarki">Nur Pratap Karki</a>
</div>