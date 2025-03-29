<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Insurance Management System Nepal</title>
  <style>
    :root {
      --primary: #3498db;
      --secondary: #2c3e50;
      --accent: #e74c3c;
      --light: #ecf0f1;
      --success: #2ecc71;
      --warning: #f39c12;
      --dark: #1a1a1a;
    }
    
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      line-height: 1.6;
      color: var(--dark);
      background-color: var(--light);
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }
    
    header {
      text-align: center;
      margin-bottom: 30px;
      padding: 20px;
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      color: white;
      border-radius: 10px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    h1 {
      font-size: 2.5rem;
      margin-bottom: 10px;
    }
    
    .subtitle {
      font-size: 1.2rem;
      opacity: 0.9;
    }
    
    .badges {
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 10px;
      margin: 20px 0;
    }
    
    .badge {
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
      color: white;
      background-color: var(--secondary);
      display: flex;
      align-items: center;
      gap: 5px;
    }
    
    .badge.blue { background-color: #3498db; }
    .badge.green { background-color: #2ecc71; }
    .badge.yellow { background-color: #f1c40f; }
    .badge.red { background-color: #e74c3c; }
    
    .main-container {
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
    }
    
    @media (min-width: 768px) {
      .main-container {
        grid-template-columns: 1fr 3fr;
      }
    }
    
    nav {
      background-color: white;
      border-radius: 10px;
      padding: 20px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    nav h2 {
      margin-bottom: 15px;
      color: var(--secondary);
      border-bottom: 2px solid var(--primary);
      padding-bottom: 8px;
    }
    
    nav ul {
      list-style: none;
    }
    
    nav li {
      margin-bottom: 10px;
    }
    
    nav a {
      color: var(--secondary);
      text-decoration: none;
      display: block;
      padding: 8px 10px;
      border-radius: 5px;
      transition: all 0.3s ease;
    }
    
    nav a:hover {
      background-color: var(--light);
      padding-left: 15px;
      color: var(--primary);
    }
    
    main {
      background-color: white;
      border-radius: 10px;
      padding: 30px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .section {
      margin-bottom: 40px;
    }
    
    h2 {
      color: var(--secondary);
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    h3 {
      color: var(--primary);
      margin: 15px 0 10px 0;
    }
    
    p {
      margin-bottom: 15px;
    }
    
    .feature-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 20px;
      margin: 20px 0;
    }
    
    .feature-card {
      background-color: var(--light);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .feature-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    }
    
    .feature-card h3 {
      font-size: 1.2rem;
      margin-bottom: 10px;
      color: var(--secondary);
    }
    
    .feature-icon {
      display: block;
      font-size: 2rem;
      margin-bottom: 15px;
      color: var(--primary);
    }
    
    .code-block {
      background-color: var(--dark);
      color: white;
      border-radius: 8px;
      padding: 15px;
      margin: 15px 0;
      overflow-x: auto;
      font-family: Consolas, Monaco, 'Andale Mono', monospace;
      line-height: 1.4;
    }
    
    .code-comment {
      color: #6c757d;
    }
    
    .tabs {
      margin: 20px 0;
    }
    
    .tab-links {
      display: flex;
      gap: 10px;
      margin-bottom: 10px;
      overflow-x: auto;
      padding-bottom: 5px;
    }
    
    .tab-link {
      padding: 10px 15px;
      background-color: var(--light);
      border-radius: 5px;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: 500;
      white-space: nowrap;
    }
    
    .tab-link.active {
      background-color: var(--primary);
      color: white;
    }
    
    .tab-content {
      display: none;
      background-color: var(--light);
      padding: 20px;
      border-radius: 8px;
      animation: fadeIn 0.3s ease;
    }
    
    .tab-content.active {
      display: block;
    }
    
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    
    .btn {
      display: inline-block;
      padding: 10px 20px;
      background-color: var(--primary);
      color: white;
      border-radius: 5px;
      text-decoration: none;
      font-weight: 500;
      transition: all 0.3s ease;
      cursor: pointer;
      border: none;
      margin: 5px 0;
    }
    
    .btn:hover {
      background-color: #2980b9;
      transform: translateY(-2px);
    }
    
    .btn-secondary {
      background-color: var(--secondary);
    }
    
    .btn-secondary:hover {
      background-color: #1a2530;
    }
    
    .steps {
      counter-reset: step;
      margin: 20px 0;
    }
    
    .step {
      margin-bottom: 15px;
      padding-left: 50px;
      position: relative;
    }
    
    .step::before {
      counter-increment: step;
      content: counter(step);
      position: absolute;
      left: 0;
      top: 0;
      width: 35px;
      height: 35px;
      background-color: var(--primary);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }
    
    .toggle-content {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.3s ease;
    }
    
    .toggle.active + .toggle-content {
      max-height: 500px;
    }
    
    .toggle {
      background-color: var(--light);
      padding: 10px 15px;
      border-radius: 5px;
      margin-top: 10px;
      cursor: pointer;
      position: relative;
      font-weight: 500;
    }
    
    .toggle::after {
      content: '+';
      position: absolute;
      right: 15px;
      transition: transform 0.3s ease;
    }
    
    .toggle.active::after {
      transform: rotate(45deg);
    }
    
    footer {
      text-align: center;
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #ddd;
      font-size: 0.9rem;
      color: #666;
    }
    
    .expandable-image {
      max-width: 100%;
      cursor: pointer;
      border-radius: 8px;
      transition: transform 0.3s ease;
    }
    
    .expandable-image:hover {
      transform: scale(1.02);
    }
  </style>
</head>
<body>

  <header>
    <h1>🇳🇵 Insurance Management System</h1>
    <p class="subtitle">A comprehensive solution for the Nepali insurance market</p>
    
    <div class="badges">
      <div class="badge blue">
        <span>Django 4.x</span>
      </div>
      <div class="badge green">
        <span>PostgreSQL 13+</span>
      </div>
      <div class="badge yellow">
        <span>Version 1.0.0</span>
      </div>
      <div class="badge red">
        <span>MIT License</span>
      </div>
    </div>
  </header>

  <div class="main-container">
    <nav>
      <h2>📋 Contents</h2>
      <ul>
        <li><a href="#overview">Overview</a></li>
        <li><a href="#features">Key Features</a></li>
        <li><a href="#architecture">Architecture</a></li>
        <li><a href="#tech-stack">Tech Stack</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#modules">Core Modules</a></li>
        <li><a href="#admin">Admin Guide</a></li>
        <li><a href="#security">Security</a></li>
        <li><a href="#compliance">Regulatory Compliance</a></li>
        <li><a href="#license">License</a></li>
      </ul>
    </nav>

    <main>
      <section id="overview" class="section">
        <h2>📋 Overview</h2>
        <p>The Insurance Management System is a robust, enterprise-grade application designed specifically for the Nepali insurance market. It streamlines the entire insurance lifecycle from policy creation to claims settlement, surrender processing, and regulatory compliance.</p>
        
        <img class="expandable-image" src="/api/placeholder/800/300" alt="Insurance Management System Dashboard">
      </section>

      <section id="features" class="section">
        <h2>✨ Key Features</h2>
        
        <div class="feature-grid">
          <div class="feature-card">
            <span class="feature-icon">📝</span>
            <h3>Policy Administration</h3>
            <p>Create and manage diverse policy types with customizable parameters</p>
          </div>
          
          <div class="feature-card">
            <span class="feature-icon">💰</span>
            <h3>Premium Management</h3>
            <p>Automated calculation with Nepal-specific tax compliance</p>
          </div>
          
          <div class="feature-card">
            <span class="feature-icon">⚠️</span>
            <h3>Claims Processing</h3>
            <p>Complete workflow from submission to settlement</p>
          </div>
          
          <div class="feature-card">
            <span class="feature-icon">👥</span>
            <h3>Agent Network</h3>
            <p>Commission tracking, licensing, and performance analytics</p>
          </div>
          
          <div class="feature-card">
            <span class="feature-icon">💸</span>
            <h3>Loan Management</h3>
            <p>Policy loans with interest calculation</p>
          </div>
          
          <div class="feature-card">
            <span class="feature-icon">📄</span>
            <h3>Surrender Processing</h3>
            <p>GSV/SSV calculations with certificate generation</p>
          </div>
          
          <div class="feature-card">
            <span class="feature-icon">⚖️</span>
            <h3>Regulatory Compliance</h3>
            <p>Built-in features for Beema Samiti requirements</p>
          </div>
          
          <div class="feature-card">
            <span class="feature-icon">📊</span>
            <h3>Comprehensive Reporting</h3>
            <p>Business intelligence across all operations</p>
          </div>
        </div>
      </section>
      
      <section id="architecture" class="section">
        <h2>🏗️ Architecture</h2>
        
        <p>The system follows Django's MVT (Model-View-Template) architecture with:</p>
        
        <ul>
          <li><strong>Role-based access control</strong> for different stakeholder types</li>
          <li><strong>Customized Django admin</strong> for insurance-specific operations</li>
          <li><strong>PostgreSQL database</strong> for robust data integrity</li>
          <li><strong>Responsive frontend</strong> for both staff and policyholder access</li>
        </ul>
        
        <div class="toggle">View Architecture Diagram</div>
        <div class="toggle-content">
          <img class="expandable-image" src="/api/placeholder/800/400" alt="System Architecture Diagram">
        </div>
      </section>
      
      <section id="tech-stack" class="section">
        <h2>🛠️ Tech Stack</h2>
        
        <div class="tabs">
          <div class="tab-links">
            <div class="tab-link active" data-tab="backend">Backend</div>
            <div class="tab-link" data-tab="frontend">Frontend</div>
            <div class="tab-link" data-tab="database">Database</div>
            <div class="tab-link" data-tab="deployment">Deployment</div>
          </div>
          
          <div class="tab-content active" id="backend">
            <h3>Backend Technologies</h3>
            <ul>
              <li><strong>Django 4.x</strong> - Web framework</li>
              <li><strong>Django REST Framework</strong> - API development</li>
              <li><strong>Celery</strong> - Task scheduling</li>
              <li><strong>Redis</strong> - Caching and message broker</li>
            </ul>
          </div>
          
          <div class="tab-content" id="frontend">
            <h3>Frontend Technologies</h3>
            <ul>
              <li><strong>HTML5/CSS3</strong> - Structure and styling</li>
              <li><strong>JavaScript/jQuery</strong> - Interactive components</li>
              <li><strong>Bootstrap</strong> - Responsive design</li>
              <li><strong>Chart.js</strong> - Data visualization</li>
            </ul>
          </div>
          
          <div class="tab-content" id="database">
            <h3>Database Technologies</h3>
            <ul>
              <li><strong>PostgreSQL 13+</strong> - Primary database</li>
              <li><strong>Django ORM</strong> - Object-relational mapping</li>
              <li><strong>Database migrations</strong> - Schema management</li>
              <li><strong>Backup tools</strong> - Data protection</li>
            </ul>
          </div>
          
          <div class="tab-content" id="deployment">
            <h3>Deployment Technologies</h3>
            <ul>
              <li><strong>Docker</strong> - Containerization</li>
              <li><strong>Nginx</strong> - Web server</li>
              <li><strong>Gunicorn</strong> - WSGI server</li>
              <li><strong>GitHub Actions</strong> - CI/CD pipeline</li>
            </ul>
          </div>
        </div>
      </section>
      
      <section id="installation" class="section">
        <h2>🚀 Getting Started</h2>
        
        <h3>Prerequisites</h3>
        <ul>
          <li>Python 3.8+</li>
          <li>PostgreSQL 13+</li>
          <li>Git</li>
        </ul>
        
        <h3>Installation</h3>
        <div class="steps">
          <div class="step">
            <p><strong>Clone repository</strong></p>
            <div class="code-block">
              git clone https://github.com/nurpratapkarki/insurance-management.git<br>
              cd insurance-management
            </div>
          </div>
          
          <div class="step">
            <p><strong>Set up virtual environment</strong></p>
            <div class="code-block">
              python -m venv venv<br>
              source venv/bin/activate  <span class="code-comment"># On Windows: venv\Scripts\activate</span>
            </div>
          </div>
          
          <div class="step">
            <p><strong>Install dependencies</strong></p>
            <div class="code-block">
              pip install -r requirements.txt
            </div>
          </div>
          
          <div class="step">
            <p><strong>Configure environment</strong></p>
            <div class="code-block">
              <span class="code-comment"># Create .env file with the following content:</span><br>
              DEBUG=True<br>
              SECRET_KEY=your-secret-key<br>
              DATABASE_URL=postgres://username:password@localhost:5432/insurance_db
            </div>
          </div>
          
          <div class="step">
            <p><strong>Run migrations</strong></p>
            <div class="code-block">
              python manage.py migrate
            </div>
          </div>
          
          <div class="step">
            <p><strong>Create admin user</strong></p>
            <div class="code-block">
              python manage.py createsuperuser
            </div>
          </div>
          
          <div class="step">
            <p><strong>Launch server</strong></p>
            <div class="code-block">
              python manage.py runserver
            </div>
            <p>Visit <code>http://localhost:8000/admin/</code> to access the system.</p>
          </div>
        </div>
      </section>
      
      <section id="modules" class="section">
        <h2>📊 Core Modules</h2>
        
        <div class="tabs">
          <div class="tab-links">
            <div class="tab-link active" data-tab="user">User Management</div>
            <div class="tab-link" data-tab="policy">Policy Management</div>
            <div class="tab-link" data-tab="premium">Premium Management</div>
            <div class="tab-link" data-tab="claims">Claims Processing</div>
            <div class="tab-link" data-tab="loans">Loan Management</div>
            <div class="tab-link" data-tab="agents">Agent Management</div>
            <div class="tab-link" data-tab="surrender">Surrender Process</div>
          </div>
          
          <div class="tab-content active" id="user">
            <h3>👥 User Management</h3>
            <p>Multi-level user hierarchy with specialized roles:</p>
            <ul>
              <li><strong>Superadmins</strong> - Complete system access</li>
              <li><strong>Company Admins</strong> - Organization-wide management</li>
              <li><strong>Branch Admins</strong> - Branch-specific operations</li>
              <li><strong>Underwriters</strong> - Risk assessment and approvals</li>
              <li><strong>Agents</strong> - Policy sales and customer management</li>
              <li><strong>Policyholders</strong> - Self-service portal</li>
            </ul>
          </div>
          
          <div class="tab-content" id="policy">
            <h3>📝 Policy Management</h3>
            <p>Configure and manage all aspects of insurance policies:</p>
            <ul>
              <li>Multiple policy types (Term, Endowment, etc.)</li>
              <li>Customizable policy parameters</li>
              <li>Document management</li>
              <li>Underwriting workflows</li>
              <li>Policy lifecycle tracking</li>
            </ul>
          </div>
          
          <div class="tab-content" id="premium">
            <h3>💰 Premium Management</h3>
            <p>Comprehensive premium handling:</p>
            <ul>
              <li>Risk-based calculation engine</li>
              <li>Multiple payment frequencies</li>
              <li>Late payment processing</li>
              <li>Nepal tax compliance (VAT, service tax)</li>
              <li>Receipt generation</li>
            </ul>
          </div>
          
          <div class="tab-content" id="claims">
            <h3>⚠️ Claims Processing</h3>
            <p>End-to-end claims workflow:</p>
            <ul>
              <li>Multi-stage verification</li>
              <li>Document management</li>
              <li>Benefit calculation</li>
              <li>Loan adjustment</li>
              <li>Payment tracking</li>
            </ul>
          </div>
          
          <div class="tab-content" id="loans">
            <h3>💸 Loan Management</h3>
            <p>Policy-secured loan processing:</p>
            <ul>
              <li>Eligibility calculation</li>
              <li>Interest accrual</li>
              <li>Repayment tracking</li>
              <li>Integration with claims/surrender</li>
            </ul>
          </div>
          
          <div class="tab-content" id="agents">
            <h3>🤝 Agent Management</h3>
            <p>Complete agent lifecycle:</p>
            <ul>
              <li>Licensing and credentials</li>
              <li>Performance tracking</li>
              <li>Commission calculation</li>
              <li>Hierarchical structures</li>
              <li>Document storage</li>
            </ul>
          </div>
          
          <div class="tab-content" id="surrender">
            <h3>📄 Surrender Processing</h3>
            <p>Handle policy surrenders:</p>
            <ul>
              <li>Calculation of surrender values</li>
              <li>Loan adjustment</li>
              <li>Documentation</li>
              <li>Certificate generation</li>
              <li>Multi-step approval workflow</li>
            </ul>
          </div>
        </div>
      </section>
      
      <section id="admin" class="section">
        <h2>👩‍💼 Admin Guide</h2>
        
        <h3>Main Administrative Sections</h3>
        <ul>
          <li><strong>Dashboard</strong> - <code>/admin/</code></li>
          <li><strong>Policy Management</strong> - <code>/admin/app/policyholder/</code></li>
          <li><strong>Premium Management</strong> - <code>/admin/app/premiumpayment/</code></li>
          <li><strong>Claims Management</strong> - <code>/admin/app/claimrequest/</code></li>
          <li><strong>Loan Management</strong> - <code>/admin/app/loan/</code></li>
          <li><strong>Surrender Management</strong> - <code>/admin/app/policysurrender/</code></li>
          <li><strong>Agent Management</strong> - <code>/admin/app/salesagent/</code></li>
          <li><strong>Reporting</strong> - Various report-specific URLs</li>
        </ul>
        
        <h3>Special Features</h3>
        <ul>
          <li><strong>Surrender Certificate Printing</strong> - Available from surrender detail page</li>
          <li><strong>Policy Renewal</strong> - Access via renewal list page</li>
          <li><strong>OTP Authentication</strong> - For sensitive operations</li>
          <li><strong>Audit Logging</strong> - Tracks all system activities</li>
        </ul>
      </section>
      
      <section id="security" class="section">
        <h2>🔐 Security Features</h2>
        
        <ul>
          <li><strong>Role-based access control</strong> - Users can only access permitted modules</li>
          <li><strong>Data encryption</strong> - Sensitive data is encrypted at rest</li>
          <li><strong>Session management</strong> - Security settings for session timeouts</li>
          <li><strong>Comprehensive audit logging</strong> - Tracks all sensitive operations</li>
          <li><strong>Automated backups</strong> - Regular database backups</li>
        </ul>
      </section>
      
      <section id="compliance" class="section">
        <h2>⚖️ Regulatory Compliance</h2>
        
        <p>Designed specifically for Nepal's insurance market:</p>
        <ul>
          <li><strong>Beema Samiti (Insurance Board)</strong> compliance</li>
          <li><strong>Nepal-specific tax handling</strong> (VAT, service tax, TDS)</li>
          <li><strong>Required regulatory documentation</strong></li>
          <li><strong>Statutory reporting</strong></li>
        </ul>
      </section>
      
      <section id="license" class="section">
        <h2>📝 License</h2>
        
        <p>This project is licensed under the MIT License - see the LICENSE file for details.</p>
      </section>
    </main>
  </div>
  
  <footer>
    <p>Developed by <a href="https://github.com/nurpratapkarki">Nur Pratap Karki</a> | © 2025 All Rights Reserved</p>
  </footer>

  <script>
    // Tab functionality
    document.querySelectorAll('.tab-link').forEach(tab => {
      tab.addEventListener('click', () => {
        // Remove active class from all tabs
        document.querySelectorAll('.tab-link').forEach(t => {
          t.classList.remove('active');
        });
        
        // Add active class to clicked tab
        tab.classList.add('active');
        
        // Hide all tab content
        document.querySelectorAll('.tab-content').forEach(content => {
          content.classList.remove('active');
        });
        
        // Show corresponding tab content
        const tabId = tab.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
      });
    });
    
    // Toggle functionality
    document.querySelectorAll('.toggle').forEach(toggle => {
      toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
      });
    });
    
    // Expandable images
    document.querySelectorAll('.expandable-image').forEach(img => {
      img.addEventListener('click', () => {
        if (img.style.maxWidth === '100%' || img.style.maxWidth === '') {
          img.style.position = 'relative';
          img.style.zIndex = '1000';
          img.style.maxWidth = '150%';
          img.style.boxShadow = '0 0 20px rgba(0,0,0,0.3)';
        } else {
          img.style.position = '';
          img.style.zIndex = '';
          img.style.maxWidth = '100%';
          img.style.boxShadow = '';
        }
      });
    });
  </script>

</body>
</html>