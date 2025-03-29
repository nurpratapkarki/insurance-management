# 🇳🇵 Insurance Management System

A comprehensive solution for the Nepali insurance market

![Version](https://img.shields.io/badge/version-1.0.0-yellow)
![Django](https://img.shields.io/badge/Django-4.x-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-green)
![License](https://img.shields.io/badge/license-MIT-red)

## 📋 Overview

The Insurance Management System is a robust, enterprise-grade application designed specifically for the Nepali insurance market. It streamlines the entire insurance lifecycle from policy creation to claims settlement, surrender processing, and regulatory compliance.

## ✨ Key Features

- **📝 Policy Administration**: Create and manage diverse policy types with customizable parameters
- **💰 Premium Management**: Automated calculation with Nepal-specific tax compliance
- **⚠️ Claims Processing**: Complete workflow from submission to settlement
- **👥 Agent Network**: Commission tracking, licensing, and performance analytics
- **💸 Loan Management**: Policy loans with interest calculation
- **📄 Surrender Processing**: GSV/SSV calculations with certificate generation
- **⚖️ Regulatory Compliance**: Built-in features for Beema Samiti requirements
- **📊 Comprehensive Reporting**: Business intelligence across all operations

## 🏗️ Architecture

The system follows Django's MVT (Model-View-Template) architecture with:

- **Role-based access control** for different stakeholder types
- **Customized Django admin** for insurance-specific operations
- **PostgreSQL database** for robust data integrity
- **Responsive frontend** for both staff and policyholder access

## 🛠️ Tech Stack

### Backend
- **Django 4.x** - Web framework
- **Django REST Framework** - API development
- **Celery** - Task scheduling
- **Redis** - Caching and message broker

### Frontend
- **HTML5/CSS3** - Structure and styling
- **JavaScript/jQuery** - Interactive components
- **Bootstrap** - Responsive design
- **Chart.js** - Data visualization

### Database
- **PostgreSQL 13+** - Primary database
- **Django ORM** - Object-relational mapping
- **Database migrations** - Schema management
- **Backup tools** - Data protection

### Deployment
- **Docker** - Containerization
- **Nginx** - Web server
- **Gunicorn** - WSGI server
- **GitHub Actions** - CI/CD pipeline

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL 13+
- Git

### Installation

1. **Clone repository**
```bash
git clone https://github.com/nurpratapkarki/insurance-management.git
cd insurance-management
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
# Create .env file with the following content:
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://username:password@localhost:5432/insurance_db
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create admin user**
```bash
python manage.py createsuperuser
```

7. **Launch server**
```bash
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

### 📄 Surrender Processing
Handle policy surrenders:
- Calculation of surrender values
- Loan adjustment
- Documentation
- Certificate generation
- Multi-step approval workflow

## 👩‍💼 Admin Guide

### Main Administrative Sections
- **Dashboard** - `/admin/`
- **Policy Management** - `/admin/app/policyholder/`
- **Premium Management** - `/admin/app/premiumpayment/`
- **Claims Management** - `/admin/app/claimrequest/`
- **Loan Management** - `/admin/app/loan/`
- **Surrender Management** - `/admin/app/policysurrender/`
- **Agent Management** - `/admin/app/salesagent/`
- **Reporting** - Various report-specific URLs

### Special Features
- **Surrender Certificate Printing** - Available from surrender detail page
- **Policy Renewal** - Access via renewal list page
- **OTP Authentication** - For sensitive operations
- **Audit Logging** - Tracks all system activities

## 🔐 Security Features

- **Role-based access control** - Users can only access permitted modules
- **Data encryption** - Sensitive data is encrypted at rest
- **Session management** - Security settings for session timeouts
- **Comprehensive audit logging** - Tracks all sensitive operations
- **Automated backups** - Regular database backups

## ⚖️ Regulatory Compliance

Designed specifically for Nepal's insurance market:
- **Beema Samiti (Insurance Board)** compliance
- **Nepal-specific tax handling** (VAT, service tax, TDS)
- **Required regulatory documentation**
- **Statutory reporting**

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Developed by [Nur Pratap Karki](https://github.com/nurpratapkarki) | © 2025 All Rights Reserved