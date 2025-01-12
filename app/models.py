from django.db import models
from django.contrib.auth.models import User, AbstractUser
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from .constants import (
    GENDER_CHOICES,
    POLICY_TYPES,
    DOCUMENT_TYPES,
    PROVINCE_CHOICES,
    REASON_CHOICES,
    STATUS_CHOICES,
    TIME_PERIOD_CHOICES,
    PROCESSING_STATUS_CHOICES,
    EMPLOYEE_STATUS_CHOICES,
    EXE_FREQ_CHOICE,
    RISK_CHOICES
)


# Create your models here.
class Occupation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    risk_category = models.CharField(
        max_length=50,
        choices=[('Low', 'Low Risk'), ('Moderate', 'Moderate Risk'), ('High', 'High Risk')],
        default='Moderate'
    )

    def __str__(self):
        return self.name
    
class MortalityRate(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='mortality_rates')
    age_group_start = models.PositiveIntegerField()
    age_group_end = models.PositiveIntegerField()
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('company', 'age_group_start', 'age_group_end')

    def __str__(self):
        return f"{self.age_group_start}-{self.age_group_end}: {self.rate}%"

class Company(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='company')
    company_code = models.IntegerField(unique=True, default=1)
    address = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company', null=True, blank=True)
    email = models.EmailField(max_length=255)
    is_active = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=20)

    def __str__(self):
        return self.name

        class Meta:
            verbose_name = 'Company'
            verbose_name_plural = 'Companies'
            indexes = [
                models.Index(fields=['name']),
            ]


# Branch Model

class Branch(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    branch_code = models.IntegerField(unique=True, default=1)
    location = models.CharField(max_length=255, null=True, blank=True)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='branches', default=1)
    manager = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='branch_manager', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['company']),
        ]


# Basic Information about Insurance Policies

class InsurancePolicy(models.Model):
    company = models.ForeignKey(
        'Company', on_delete=models.CASCADE, related_name='insurance_policies')
    name = models.CharField(max_length=200)
    min_sum_assured = models.DecimalField(max_digits=12, decimal_places=2, default=500.00)
    max_sum_assured = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    quarterly_loading = models.DecimalField(max_digits=5, decimal_places=2, default=1.5)  # Quarterly loading %
    semi_annual_loading = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)  # Semi-annual loading %
    adb_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # ADB charge %
    ptd_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # PTD charge %
    include_adb = models.BooleanField(default=False)
    include_ptd = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Insurance Policy"
        verbose_name_plural = "Insurance Policies"


#  Agent Application

class AgentApplication(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(
        Company,  on_delete=models.CASCADE, related_name='agent_applications', default=1)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='agent_applications', default=1)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=50)
    father_name = models.CharField(max_length=200)
    mother_name = models.CharField(max_length=200)
    grand_father_name = models.CharField(max_length=200, null=True, blank=True)
    grand_mother_name = models.CharField(max_length=200, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default='Male')
    email = models.EmailField(max_length=200, unique=True)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=200)
    resume = models.FileField(
        upload_to='agent_application', null=True, blank=True)
    citizenship_front = models.ImageField(
        upload_to='agent_application', null=True, blank=True)
    citizenship_back = models.ImageField(
        upload_to='agent_application', null=True, blank=True)
    license_front = models.ImageField(
        upload_to='agent_application', null=True, blank=True)
    license_back = models.ImageField(
        upload_to='agent_application', null=True, blank=True)
    pp_photo = models.ImageField(
        upload_to='agent_application', null=True, blank=True)
    license_number = models.CharField(max_length=50, null=True, blank=True)
    license_issue_date = models.DateField(null=True, blank=True)
    license_expiry_date = models.DateField(null=True, blank=True)
    license_type = models.CharField(max_length=50, null=True, blank=True)
    license_issue_district = models.CharField(
        max_length=50, null=True, blank=True)
    license_issue_zone = models.CharField(max_length=50, null=True, blank=True)
    license_issue_province = models.CharField(
        max_length=50, null=True, blank=True)
    license_issue_country = models.CharField(
        max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateField(default=date.today)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = 'Agent Application'
        verbose_name_plural = 'Agent Applications'
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['branch']),
            models.Index(fields=['status']),
        ]


# Sales Agent

class SalesAgent(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='sales_agents', default=1)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='sales_agents', default=1)
    application = models.OneToOneField(
        AgentApplication,
        on_delete=models.SET_NULL,
        related_name='sales_agent',
        null=True,
        blank=True
    )

    agent_code = models.CharField(max_length=50, unique=True, default=1)
    is_active = models.BooleanField(default=True)
    joining_date = models.DateField(default=date.today)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)
    total_policies_sold = models.IntegerField(default=0)
    total_premium_collected = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00)
    last_policy_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.CharField(
        max_length=200, null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=EMPLOYEE_STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        if self.application:
            return f"{self.application.first_name} {self.application.last_name} ({self.agent_code})"
        return self.agent_code

    def get_full_name(self):
        if self.application:
            return f"{self.application.first_name} {self.application.last_name}"
        return None

    class Meta:
        verbose_name = 'Sales Agent'
        verbose_name_plural = 'Sales Agents'
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['branch']),
            models.Index(fields=['total_policies_sold']),
            models.Index(fields=['status']),
        ]


class PolicyHolder(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(
        Company,  on_delete=models.CASCADE, related_name='policy_holders', default=1)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, blank=True, null=True)
    policy_number = models.IntegerField(
        unique=True, default='', blank=True, null=True)
    agent = models.ForeignKey(
        SalesAgent, on_delete=models.CASCADE, null=True, blank=True, default='')
    policy = models.ForeignKey(
        InsurancePolicy, related_name='policy_holders', on_delete=models.CASCADE, blank=True, null=True
    )
    duration_years = models.PositiveIntegerField(default=1)
    sum_assured = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    first_name = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, blank=True, null=True, choices=[
                              ("M", "Male"), ("F", "Female"), ("O", "Other")])
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(editable=False, null=True)
    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )
    emergency_contact_name = models.CharField(
        max_length=200, blank=True, null=True)
    emergency_contact_number = models.CharField(
        max_length=15, blank=True, null=True)

    document_number = models.CharField(
        max_length=50,
        default=1
    )
    document_type = models.CharField(
        max_length=111, blank=True, null=True, choices=DOCUMENT_TYPES)
    document_front = models.ImageField(
        upload_to="policyHolder")
    document_back = models.ImageField(
        upload_to="policyHolder")
    pan_Number = models.CharField(max_length=20, blank=True, null=True)
    pan_front = models.ImageField(
        upload_to='policy_holders', null=True, blank=True)
    pan_back = models.ImageField(
        upload_to='policy_holders', null=True, blank=True)

    pp_photo = models.ImageField(
        upload_to='policyHolder')
    dietary_habits = models.TextField(blank=True, null=True)
    nominee_name = models.CharField(max_length=200, null=True, blank=True)
    nominee_document_type = models.CharField(
        max_length=111, blank=True, null=True, choices=DOCUMENT_TYPES)
    nominee_document_number = models.PositiveIntegerField(
        null=True, blank=True)
    nominee_document_front = models.ImageField(
        upload_to="policyHolder")
    nominee_document_back = models.ImageField(
        upload_to="policyHolder")
    nominee_pp_photo = models.ImageField(
        upload_to='policyHolder')
    nominee_relation = models.CharField(max_length=255)
    provience = models.CharField(max_length=255, choices=PROVINCE_CHOICES)
    district = models.CharField(max_length=255)
    municipality = models.CharField(max_length=255)
    ward = models.CharField(max_length=255)
    nearest_hospital = models.CharField(max_length=255, blank=True, null=True)
    natural_hazard_exposure = models.CharField(
        max_length=50,
        choices= RISK_CHOICES,
        blank=True,
        null=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    work_environment_risk = models.CharField(
    max_length=50, 
    choices=RISK_CHOICES, 
    blank=True, 
    null=True
)
    


    policy = models.ForeignKey(
        InsurancePolicy, related_name='policy_holders', on_delete=models.CASCADE, blank=True, null=True
    )
    heath_history = models.CharField(max_length=500, null=True, blank=True)
    habits = models.CharField(max_length=500, null=True, blank=True)
    exercise_frequency = models.CharField(
        max_length=50,
        choices=EXE_FREQ_CHOICE,
        blank=True,
        null=True
    )
    alcholic = models.BooleanField(default= False)
    smoker = models.BooleanField(default= False)
    include_adb = models.BooleanField(default=False)
    include_ptd = models.BooleanField(default=False)
    past_medical_report = models.FileField(upload_to='policy_holders', null= True,blank= True)
    family_medical_history = models.TextField(null= True, blank=True)
    recent_medical_reports = models.FileField(upload_to='policy_holders', blank=True, null=True)
    yearly_income = models.CharField(max_length=455, default=500000)
    occupation = models.ForeignKey(Occupation, on_delete=models.SET_NULL, null=True, blank=True)
    assets_details = models.TextField(max_length= 5000, null=True, blank=True)
    payment_interval = models.CharField(
        max_length=20,
        choices=[("Single", "Single"), ("quarterly", "Quarterly"),
                 ("semi_annual", "Semi-Annual"), ("annual", "Annual")],
        default="annual"
    )
    payment_mode = models.CharField(
        max_length=50,
        choices=[("Cash", "Cash"), ("Bank Transfer", "Bank Transfer"),
                 ("Online Payment", "Online Payment")],
        default="Online Payment"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(
        max_length=50, choices=PROCESSING_STATUS_CHOICES, default="Due")

    @property
    def age(self):
        from datetime import date
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    def save(self, *args, **kwargs):
        if self.status == 'Active' and not self.policy_number:
            # Generate policy number if not already set
            if not self.branch:
                raise ValueError("Branch is required to generate the policy number.")
            last_holder = PolicyHolder.objects.filter(branch=self.branch).order_by('-id').first()
            last_number = int(last_holder.policy_number.split(self.branch.branch_code)[-1]) if last_holder else 0
            self.policy_number = f"{self.branch.branch_code}{str(last_number + 1).zfill(5)}"

        super().save(*args, **kwargs)
    def clean(self):
        # Validate the age range
        if self.date_of_birth:
            today = date.today()
            age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (
                    self.date_of_birth.month, self.date_of_birth.day)
            )
            if age < 18 or age > 60:
                raise ValidationError(
                    f"Age must be between 18 and 60. The provided age is {
                        age}."
                )

    def save(self, *args, **kwargs):
        

        if not self.policy_number:
            # Fetch last policy for the same company and branch
            last_policy = PolicyHolder.objects.filter(
                company=self.company, branch=self.branch).order_by('id').last()

        # Extract the last number from the last policy
            last_number = int(
                last_policy.policy_number[-6:]) if last_policy and last_policy.policy_number[-6:].isdigit() else 0

        # Generate new policy number
            self.policy_number = f"{self.company.company_code}{
                self.branch.branch_code}{str(last_number + 1).zfill(5)}"

            super().save(*args, **kwargs)

        # Calculate age automatically
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = 'Policy Holder'
        verbose_name_plural = 'Policy Holders'
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['agent']),
            models.Index(fields=['policy']),
            models.Index(fields=['payment_status']),
        ]
# claim requestes


class ClaimRequest(models.Model):

    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(
        Company,  on_delete=models.CASCADE, related_name='claim_requests', default=1)
    policy_holder = models.ForeignKey(
        'PolicyHolder', related_name='claim_requests', on_delete=models.CASCADE, null=True, blank=True
    )
    claim_date = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="Pending")
    bill = models.ImageField(
        upload_to='claim_processing', null=True, blank=True)
    policy_copy = models.ImageField(
        upload_to='claim_processing', default=False)
    health_report = models.ImageField(
        upload_to='claim_processing', default=False)
    reason = models.CharField(
        max_length=50, choices=REASON_CHOICES, default='Others')
    other_reason = models.CharField(max_length=500, null=True, blank=True)
    claim_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=500.00)

    def __str__(self):
        return f"Claim {self.id} - {self.policy_holder}"

    class Meta:
        verbose_name = 'Claim Request'
        verbose_name_plural = 'Claim Requests'


# Claim Processing
class ClaimProcessing(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(
        Company,  on_delete=models.CASCADE, related_name='claim_processings', default=1)

    claim_request = models.ForeignKey(
        ClaimRequest, related_name='claim_processings', on_delete=models.CASCADE, null=True, blank=True
    )
    processing_status = models.CharField(
        max_length=50, choices=[("In Progress", "In Progress"), ("Completed", "Completed")]
    )
    processing_date = models.DateField(auto_now=True)

    def __str__(self):
        return f"Processing {self.id} - {self.processing_status}"

    class Meta:
        verbose_name = 'Claim Processing'
        verbose_name_plural = 'Claim Processings'

# Employee and Roles
class EmployeePosition(models.Model):
    id = models.BigAutoField(primary_key=True)
    position = models.CharField(max_length=50)

    def __str__(self):
        return self.position

    class Meta:
        verbose_name = 'Employee Position'
        verbose_name_plural = 'Employee Positions'


class Employee(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(
        Company,  on_delete=models.CASCADE, related_name='employees', default=1)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    employee_position = models.ForeignKey(
        EmployeePosition, related_name='employees', on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'


# Payment Processing
class PaymentProcessing(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(
        Company,  on_delete=models.CASCADE, related_name='payment_processings', default=1)

    name = models.CharField(max_length=200)
    processing_status = models.CharField(
        max_length=50, choices=[("Pending", "Pending"), ("Completed", "Completed")], default="Pending"
    )
    claim_request = models.ForeignKey(
        ClaimRequest, on_delete=models.CASCADE, null=True, blank=True
    )
    date_of_processing = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Payment Processing'
        verbose_name_plural = 'Payment Processings'

# Underwriting Process Or report
class Underwriting(models.Model):
    policy_holder = models.OneToOneField('PolicyHolder', on_delete=models.CASCADE, related_name='underwriting')
    risk_assessment_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    remarks = models.TextField(null=True, blank=True)
    risk_category = models.CharField(
        max_length=50,
        choices=[('Low', 'Low Risk'), ('Moderate', 'Moderate Risk'), ('High', 'High Risk')],
        default='Moderate'
    )

    def save(self, *args, **kwargs):
        self.risk_assessment_score = self.calculate_risk()
        self.risk_category = self.determine_risk_category()
        super().save(*args, **kwargs)

    def calculate_risk(self):
        # Example: Calculate risk score based on age and occupation
        age = self.policy_holder.age
        occupation_risk = {
            'Low': 10,
            'Moderate': 20,
            'High': 30,
        }.get(self.policy_holder.occupation.risk_category, 20)
        return min(age + occupation_risk, 100)  # Capping at 100

    def determine_risk_category(self):
        score = self.risk_assessment_score
        if score < 40:
            return 'Low'
        elif score < 70:
            return 'Moderate'
        return 'High'
class PremiumPayment(models.Model):
    policy_holder = models.ForeignKey('PolicyHolder', on_delete=models.CASCADE, related_name='premium_payments')
    annual_premium = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    interval_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    def get_mortality_rate(self):
        """Get the appropriate mortality rate based on policy holder's age"""
        age = self.policy_holder.age
        company = self.policy_holder.company
        
        try:
            mortality_rate = MortalityRate.objects.filter(
                company=company,
                age_group_start__lte=age,
                age_group_end__gte=age
            ).first()
            
            if mortality_rate:
                return mortality_rate.rate
            else:
                raise ValueError(f"No mortality rate found for age {age} in company {company}")
                
        except MortalityRate.DoesNotExist:
            raise ValueError(f"No mortality rate found for age {age} in company {company}")
    
    def calculate_premium(self):
        """Calculate premium without saving"""
        policy_holder = self.policy_holder
        policy = policy_holder.policy
        sum_assured = policy_holder.sum_assured

        # Base Premium from Mortality Rate
        mortality_rate = self.get_mortality_rate()
        base_premium = sum_assured * Decimal(str(mortality_rate / 1000))

        # ADB and PTD Charges
        adb_charge = sum_assured * Decimal(policy.adb_percentage / 100) if policy.include_adb else Decimal(0)
        ptd_charge = sum_assured * Decimal(policy.ptd_percentage / 100) if policy.include_ptd else Decimal(0)

        # Total Base Premium
        total_base_premium = base_premium + adb_charge + ptd_charge

        # Loading Charges
        interval = policy_holder.payment_interval
        loading_charges = {
            'quarterly': policy.quarterly_loading,
            'semi_annual': policy.semi_annual_loading,
        }
        interval_loading = Decimal(str(loading_charges.get(interval, 0))) / 100
        annual_premium = total_base_premium * (1 + interval_loading if interval in ["quarterly", "semi_annual"] else 1)

        # Interval Payments
        interval_count = {"quarterly": 4, "semi_annual": 2, "single": 1}.get(interval, 1)
        interval_payment = (annual_premium / interval_count).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return annual_premium, interval_payment

    def save(self, *args, **kwargs):
        if not self.pk:  # Only calculate on creation
            self.annual_premium, self.interval_payment = self.calculate_premium()
        super().save(*args, **kwargs)
# Agent Report


class AgentReport(models.Model):
    agent = models.ForeignKey(SalesAgent, on_delete=models.CASCADE)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='agent_reports', default=1)
    report_date = models.DateField()
    reporting_period = models.CharField(max_length=20)
    policies_sold = models.IntegerField(default=0)
    total_premium = models.DecimalField(max_digits=12, decimal_places=2)
    commission_earned = models.DecimalField(max_digits=10, decimal_places=2)
    target_achievement = models.DecimalField(max_digits=5, decimal_places=2)
    renewal_rate = models.DecimalField(max_digits=5, decimal_places=2)
    customer_retention = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"Report for {self.agent} on {self.report_date}"

    class Meta:
        verbose_name = 'Agent Report'
        verbose_name_plural = 'Agent Reports'
# auto generate agent report


@receiver(post_save, sender=PremiumPayment)
def update_agent_report(sender, instance, **kwargs):
    agent = instance.policy_holder.agent
    if agent:
        report, created = AgentReport.objects.get_or_create(
            agent=agent,
            company=agent.company,
            report_date=date.today(),
            defaults={
                'reporting_period': 'Daily',
                'policies_sold': 0,
                'total_premium': Decimal(0.00),
                'commission_earned': Decimal(0.00),
                'target_achievement': Decimal(0.00),
                'renewal_rate': Decimal(0.00),
                'customer_retention': Decimal(0.00)
            }
        )
        # Update the report with the new payment details
        report.total_premium += Decimal(instance.amount)  # Convert to Decimal
        report.policies_sold += 1  # Increment for a new policy
        report.commission_earned += Decimal(instance.amount) * \
            agent.commission_rate / Decimal(100)  # Ensure Decimal
        report.save()

