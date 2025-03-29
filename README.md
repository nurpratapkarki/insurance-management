# <img src="https://img.shields.io/badge/🇳🇵-Nepal-e01e26" alt="Nepal Flag"> Insurance Management System

<p align="center">A comprehensive solution for the Nepali insurance market</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-yellow" alt="Version">
  <img src="https://img.shields.io/badge/Django-4.x-blue" alt="Django">
  <img src="https://img.shields.io/badge/mySQL-13+-green" alt="MySQL">
  <img src="https://img.shields.io/badge/license-MIT-red" alt="License">
</p>

## 📋 Overview

The Insurance Management System is a robust, enterprise-grade application designed specifically for the Nepali insurance market. It streamlines the entire insurance lifecycle from policy creation to claims settlement, surrender processing, and regulatory compliance.

<details>
  <summary><b>👉 View System Screenshot</b></summary>
  <p align="center">
    <i>Dashboard preview image would go here</i>
  </p>
</details>

## ✨ Key Features

<table>
  <tr>
    <td><b>📝 Policy Administration</b></td>
    <td>Create and manage diverse policy types with customizable parameters</td>
  </tr>
  <tr>
    <td><b>💰 Premium Management</b></td>
    <td>Automated calculation with Nepal-specific tax compliance</td>
  </tr>
  <tr>
    <td><b>⚠️ Claims Processing</b></td>
    <td>Complete workflow from submission to settlement</td>
  </tr>
  <tr>
    <td><b>👥 Agent Network</b></td>
    <td>Commission tracking, licensing, and performance analytics</td>
  </tr>
  <tr>
    <td><b>💸 Loan Management</b></td>
    <td>Policy loans with interest calculation</td>
  </tr>
  <tr>
    <td><b>📄 Surrender Processing</b></td>
    <td>GSV/SSV calculations with certificate generation</td>
  </tr>
  <tr>
    <td><b>⚖️ Regulatory Compliance</b></td>
    <td>Built-in features for Beema Samiti requirements</td>
  </tr>
  <tr>
    <td><b>📊 Comprehensive Reporting</b></td>
    <td>Business intelligence across all operations</td>
  </tr>
</table>

## 🏗️ Architecture

The system follows Django's MVT (Model-View-Template) architecture with:

- **Role-based access control** for different stakeholder types
- **Customized Django admin** for insurance-specific operations
- **MySQL database** for robust data integrity
- **Responsive frontend** for both staff and policyholder access

<details>
  <summary><b>👉 View Architecture Diagram</b></summary>
  <p align="center">
    <i>Architecture diagram would go here</i>
  </p>
</details>

## 🛠️ Tech Stack

<details open>
  <summary><b>Backend</b></summary>
  <ul>
    <li><b>Django 4.x</b> - Web framework</li>
    <li><b>Django REST Framework</b> - API development</li>
    <li><b>Celery</b> - Task scheduling</li>
    <li><b>Redis</b> - Caching and message broker</li>
  </ul>
</details>

<details>
  <summary><b>Frontend</b></summary>
  <ul>
    <li><b>HTML5/CSS3</b> - Structure and styling</li>
    <li><b>JavaScript/jQuery</b> - Interactive components</li>
    <li><b>Bootstrap</b> - Responsive design</li>
    <li><b>Chart.js</b> - Data visualization</li>
  </ul>
</details>

<details>
  <summary><b>Database</b></summary>
  <ul>
    <li><b>MySQL 13+</b> - Primary database</li>
    <li><b>Django ORM</b> - Object-relational mapping</li>
    <li><b>Database migrations</b> - Schema management</li>
    <li><b>Backup tools</b> - Data protection</li>
  </ul>
</details>

<details>
  <summary><b>Deployment</b></summary>
  <ul>
    <li><b>Nginx</b> - Web server</li>
    <li><b>Gunicorn</b> - WSGI server</li>
    <li><b>GitHub Actions</b> - CI/CD pipeline</li>
  </ul>
</details>

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MySQL13+
- Git

### Installation

<ol>
  <li>
    <b>Clone repository</b>
    <pre><code>git clone https://github.com/nurpratapkarki/insurance-management.git
cd insurance-management</code></pre>
  </li>
  <li>
    <b>Set up virtual environment</b>
    <pre><code>python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate</code></pre>
  </li>
  <li>
    <b>Install dependencies</b>
    <pre><code>pip install -r requirements.txt</code></pre>
  </li>
  <li>
    <b>Configure environment</b>
    <pre><code># Create .env file with the following content:
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://username:password@localhost:5432/insurance_db</code></pre>
  </li>
  <li>
    <b>Run migrations</b>
    <pre><code>python manage.py migrate</code></pre>
  </li>
  <li>
    <b>Create admin user</b>
    <pre><code>python manage.py createsuperuser</code></pre>
  </li>
  <li>
    <b>Launch server</b>
    <pre><code>python manage.py runserver</code></pre>
    Visit <code>http://localhost:8000/admin/</code> to access the system.
  </li>
</ol>

## 📊 Core Modules

<details open>
  <summary><b>👥 User Management</b></summary>
  <p>Multi-level user hierarchy with specialized roles:</p>
  <ul>
    <li><b>Superadmins</b> - Complete system access</li>
    <li><b>Company Admins</b> - Organization-wide management</li>
    <li><b>Branch Admins</b> - Branch-specific operations</li>
    <li><b>Underwriters</b> - Risk assessment and approvals</li>
    <li><b>Agents</b> - Policy sales and customer management</li>
    <li><b>Policyholders</b> - Self-service portal</li>
  </ul>
</details>

<details>
  <summary><b>📝 Policy Management</b></summary>
  <p>Configure and manage all aspects of insurance policies:</p>
  <ul>
    <li>Multiple policy types (Term, Endowment, etc.)</li>
    <li>Customizable policy parameters</li>
    <li>Document management</li>
    <li>Underwriting workflows</li>
    <li>Policy lifecycle tracking</li>
  </ul>
</details>

<details>
  <summary><b>💰 Premium Management</b></summary>
  <p>Comprehensive premium handling:</p>
  <ul>
    <li>Risk-based calculation engine</li>
    <li>Multiple payment frequencies</li>
    <li>Late payment processing</li>
    <li>Nepal tax compliance (VAT, service tax)</li>
    <li>Receipt generation</li>
  </ul>
</details>

<details>
  <summary><b>⚠️ Claims Processing</b></summary>
  <p>End-to-end claims workflow:</p>
  <ul>
    <li>Multi-stage verification</li>
    <li>Document management</li>
    <li>Benefit calculation</li>
    <li>Loan adjustment</li>
    <li>Payment tracking</li>
  </ul>
</details>

<details>
  <summary><b>💸 Loan Management</b></summary>
  <p>Policy-secured loan processing:</p>
  <ul>
    <li>Eligibility calculation</li>
    <li>Interest accrual</li>
    <li>Repayment tracking</li>
    <li>Integration with claims/surrender</li>
  </ul>
</details>

<details>
  <summary><b>🤝 Agent Management</b></summary>
  <p>Complete agent lifecycle:</p>
  <ul>
    <li>Licensing and credentials</li>
    <li>Performance tracking</li>
    <li>Commission calculation</li>
    <li>Hierarchical structures</li>
    <li>Document storage</li>
  </ul>
</details>

<details>
  <summary><b>📄 Surrender Processing</b></summary>
  <p>Handle policy surrenders:</p>
  <ul>
    <li>Calculation of surrender values</li>
    <li>Loan adjustment</li>
    <li>Documentation</li>
    <li>Certificate generation</li>
    <li>Multi-step approval workflow</li>
  </ul>
</details>

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

<p align="center">Developed by <a href="https://github.com/nurpratapkarki">Nur Pratap Karki</a> | © 2025 All Rights Reserved</p>