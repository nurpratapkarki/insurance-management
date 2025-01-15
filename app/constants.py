GENDER_CHOICES = [
    ("M", "Male"),
    ("F", "Female"),
    ("O", "Other"),
]

POLICY_TYPES = [
    ("Endownment", "Endownment"),
    ("Trem", "Trem"),
]

DOCUMENT_TYPES = [
    ('Passport', 'Passport'),
    ('Citizenship', 'Citizenship'),
]

PROVINCE_CHOICES = [
    ('Koshi', 'Koshi'),
    ('Madesh', 'Madesh'),
    ('Bagmati', 'Bagmati'),
    ('Gandaki', 'Gandaki'),
    ('Lumbini', 'Lumbini'),
    ('Karnali', 'Karnali'),
    ('Suderpachhim', 'Suderpachhim'),
]

REASON_CHOICES = [
    ('Maturity of Insurance', 'Maturity of Insurance'),
    ('Accident', 'Accident'),
    ('Critical Illness', 'Critical Illness'),
    ('Disability', 'Disability'),
    ('Others', 'Others'),
]

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Under Review', 'Under Review'),
    ('Approved', 'Approved'),
    ('Active', 'Active'),
    ('Rejected', 'Rejected'),
    ('Cancelled', 'Cancelled'),
    ('Expired', 'Expired')
]

PROCESSING_STATUS_CHOICES = [
    ("In Progress", "In Progress"),
    ("Completed", "Completed"),
]
TIME_PERIOD_CHOICES = [ ('Quarterly', 'Quarterly'), ('Yearly', 'Yearly')]
EMPLOYEE_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('TERMINATED', 'Terminated'),
        ('ON_LEAVE', 'On Leave')
    ]
EXE_FREQ_CHOICE = [("None", "None"), ("Occasional", "Occasional"), ("Regular", "Regular")]
RISK_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
PAYMENT_CHOICES = [
    ('Unpaid', 'Unpaid'),
    ('Partially Paid', 'Partially Paid'),
    ('Paid', 'Paid'),
]