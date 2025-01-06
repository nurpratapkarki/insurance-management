from django.db import models
from django.contrib.auth.models import User, AbstractUser
from datetime import date
from decimal import Decimal
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
    EMPLOYEE_STATUS_CHOICES
)


# Create your models here.

class Company(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    company_code = models.IntegerField( unique=True,default= 1)
    address = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company', null= True, blank = True)
    email = models.EmailField(max_length=255)
    is_active = models.BooleanField(default= True)
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
    branch_code = models.IntegerField( unique=True, default= 1)
    location = models.CharField(max_length=255,null = True, blank = True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches', default= 1)
    manager = models.OneToOneField(User, on_delete=models.CASCADE, related_name='branch_manager', null=True, blank=True)

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
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='insurance_policies', default=1)
    name = models.CharField(max_length=200)
    policy_type= models.CharField(max_length=50, choices=POLICY_TYPES, default='Indroment')
    min_sum_assured = models.DecimalField(max_digits=12, decimal_places=2, default=500.00)
    max_sum_assured = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    fixed_premium_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # Percentage
    adb_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # ADB charge percentage
    ptd_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # PTD charge percentage
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=False)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Insurance Policy'
        verbose_name_plural = 'Insurance Policies'
        
# Loading Charges
class LoadingCharge(models.Model):
    insurance_policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE, related_name='loading_charges')
    interval = models.CharField(
        max_length=20,
        choices=[("monthly", "Monthly"), ("quarterly", "Quarterly"), ("semi_annual", "Semi-Annual"), ("annual", "Annual")],
        unique=True
    )
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Percentage

    def __str__(self):
        return f"{self.insurance_policy.name} - {self.interval.capitalize()} - {self.percentage}%"

    class Meta:
        verbose_name = 'Loading Charge'
        verbose_name_plural = 'Loading Charges'
        unique_together = ('insurance_policy', 'interval')

        
#  Agent Application

class AgentApplication(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name= 'agent_applications', default= 1)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='agent_applications', default= 1)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=50)
    father_name = models.CharField(max_length=200)
    mother_name = models.CharField(max_length=200)
    grand_father_name = models.CharField(max_length=200, null=True, blank=True)
    grand_mother_name = models.CharField(max_length=200, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    email = models.EmailField(max_length=200, unique=True)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=200)
    resume = models.FileField(upload_to='agent_application', null=True, blank=True)
    citizenship_front = models.ImageField(upload_to='agent_application', null=True, blank=True)
    citizenship_back = models.ImageField(upload_to='agent_application', null=True, blank=True)
    license_front = models.ImageField(upload_to='agent_application', null=True, blank=True)
    license_back = models.ImageField(upload_to='agent_application', null=True, blank=True)
    pp_photo = models.ImageField(upload_to='agent_application', null=True, blank=True)
    license_number = models.CharField(max_length=50, null=True, blank=True)
    license_issue_date = models.DateField(null=True, blank=True)
    license_expiry_date = models.DateField(null=True, blank=True)
    license_type = models.CharField(max_length=50, null=True, blank=True)
    license_issue_district = models.CharField(max_length=50, null=True, blank=True)
    license_issue_zone = models.CharField(max_length=50, null=True, blank=True)
    license_issue_province = models.CharField(max_length=50, null=True, blank=True)
    license_issue_country = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
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
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_agents', default=1)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='sales_agents', default=1)
    application = models.OneToOneField(
        AgentApplication, 
        on_delete=models.SET_NULL, 
        related_name='sales_agent', 
        null=True, 
        blank=True
    )
    
    agent_code = models.CharField(max_length=50, unique=True, default=1)
    is_active = models.BooleanField(default=True)
    joining_date = models.DateField( default=date.today)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_policies_sold = models.IntegerField(default=0)
    total_premium_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    last_policy_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    termination_reason = models.CharField(max_length=200, null=True, blank=True)
    
    
    
    status = models.CharField(max_length=20, choices=EMPLOYEE_STATUS_CHOICES, default='ACTIVE')
    
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
    company = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name= 'policy_holders', default= 1)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, blank=True, null=True)
    policy_number = models.IntegerField( unique=True, default='', blank=True, null=True)
    agent = models.ForeignKey(
        SalesAgent, on_delete=models.CASCADE, null=True, blank=True, default='')
    policy = models.ForeignKey(
        InsurancePolicy, related_name='policy_holders', on_delete=models.CASCADE, blank=True, null=True
    )
    duration_years = models.PositiveIntegerField(default=1)
    sum_assured = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    first_name = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    gender = models.CharField(max_length=1, blank=True, null=True, choices=[
                              ("M", "Male"), ("F", "Female"), ("O", "Other")])
    date_of_birth = models.DateField(null=True, blank=True)  
    age = models.PositiveIntegerField(editable=False, null=True) 
    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )
    document_number = models.CharField(
        max_length=50,
    
        null=True,
        blank=True
    )
    document_type = models.CharField(max_length=111, blank=True, null=True, choices=DOCUMENT_TYPES )
    document_front = models.ImageField(
        upload_to="policyHolder", null=True, blank=True)
    document_back = models.ImageField(
        upload_to="policyHolder", null=True, blank=True)
    pp_photo = models.ImageField(
        upload_to='policyHolder', null=True, blank=True)
    nominee_name = models.CharField(max_length=200, null=True, blank=True)
    nominee_document_type = models.CharField(max_length=111, blank=True, null=True, choices= DOCUMENT_TYPES)
    nominee_document_number = models.PositiveIntegerField(null=True, blank=True)
    nominee_document_front = models.ImageField(
        upload_to="policyHolder", null=True, blank=True)
    nominee_document_back = models.ImageField(
        upload_to="policyHolder", null=True, blank=True)
    nominee_pp_photo = models.ImageField(
        upload_to='policyHolder', null=True, blank=True)
    nominee_relation = models.CharField(max_length=255, null=True, blank=True)
    provience = models.CharField(max_length=255, choices=PROVINCE_CHOICES, null=True, blank=True)
    district = models.CharField(max_length=255, null=True, blank=True)
    municipality = models.CharField(max_length=255, null=True, blank=True)
    ward = models.CharField(max_length=255, null=True, blank=True)
    policy = models.ForeignKey(
        InsurancePolicy, related_name='policy_holders', on_delete=models.CASCADE, blank=True, null=True
    )
    
    include_adb = models.BooleanField(default=False)
    include_ptd = models.BooleanField(default=False)
    
    payment_interval = models.CharField(
        max_length=20,
        choices=[("monthly", "Monthly"), ("quarterly", "Quarterly"), ("semi_annual", "Semi-Annual"), ("annual", "Annual")],
        default="annual"
    )
    payment_status = models.CharField(
        max_length=50, choices= PROCESSING_STATUS_CHOICES, default="Due")

    def clean(self):
        # Validate the age range
        if self.date_of_birth:
            today = date.today()
            age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
            if age < 18 or age > 60:
                raise ValidationError(
                    f"Age must be between 18 and 60. The provided age is {age}."
                )

    def save(self, *args, **kwargs):
        
        if not self.policy_number:
        # Fetch last policy for the same company and branch
            last_policy = PolicyHolder.objects.filter(company=self.company, branch=self.branch).order_by('id').last()
        
        # Extract the last number from the last policy
            last_number = int(last_policy.policy_number[-6:]) if last_policy and last_policy.policy_number[-6:].isdigit() else 0

        # Generate new policy number
            self.policy_number = f"{self.company.company_code}{self.branch.branch_code}{str(last_number + 1).zfill(5)}"
    
            super().save(*args, **kwargs)
    
        # Calculate age automatically
        if self.date_of_birth:
            today = date.today()
            self.age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
            # For calculating the sum assured
        if self.policy and not self.sum_assured:
            self.sum_assured = self.policy.min_sum_assured
        elif self.policy and self.sum_assured:
            # Ensure sum_assured is within allowed bounds
            if self.sum_assured < self.policy.min_sum_assured or self.sum_assured > self.policy.max_sum_assured:
                raise ValidationError(f"Sum assured must be between {self.policy.min_sum_assured} and {self.policy.max_sum_assured}.")
        super().save(*args, **kwargs)

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
    company = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name= 'claim_requests', default= 1)
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
    claim_amount = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)

    def __str__(self):
        return f"Claim {self.id} - {self.policy_holder}"

    class Meta:
        verbose_name = 'Claim Request'
        verbose_name_plural = 'Claim Requests'


# Claim Processing
class ClaimProcessing(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name= 'claim_processings', default= 1)
    
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


# Premium Payment Tracking
class PremiumPayment(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='premium_payments', default=1)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='premium_payments')
    policy_holder = models.ForeignKey(PolicyHolder, related_name="premium_payments", on_delete=models.CASCADE)
    annual_premium = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)  # Interval payment
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Track actual payments made
    payment_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=50, choices=PROCESSING_STATUS_CHOICES, default="Due")

    def calculate_premium(self):
        try:
            policy = self.policy_holder.policy
            sum_assured = self.policy_holder.sum_assured

            # Fixed premium calculation
            fixed_premium = sum_assured * Decimal(policy.fixed_premium_ratio / 100)

            # Optional charges
            adb_amount = sum_assured * Decimal(policy.adb_percentage / 100) if self.policy_holder.include_adb else Decimal(0)
            ptd_amount = sum_assured * Decimal(policy.ptd_percentage / 100) if self.policy_holder.include_ptd else Decimal(0)

            # Base annual premium
            base_annual_premium = fixed_premium + adb_amount + ptd_amount

            # Loading charges
            interval = self.policy_holder.payment_interval
            loading_charge = policy.loading_charges.filter(interval=interval).first()
            loading_percentage = Decimal(loading_charge.percentage if loading_charge else 0)

            # Final premium calculations
            loaded_annual_premium = base_annual_premium * (1 + loading_percentage / 100)
            intervals = {"monthly": 12, "quarterly": 4, "semi_annual": 2, "annual": 1}
            interval_count = intervals.get(interval, 1)
            interval_payment = loaded_annual_premium / interval_count

            return base_annual_premium, loaded_annual_premium, interval_payment
        except Exception as e:
            raise ValidationError(f"Premium calculation failed: {str(e)}")

    def save(self, *args, **kwargs):
        # Ensure annual_premium and amount are always recalculated before saving
        _, self.annual_premium, self.amount = self.calculate_premium()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.id} - {self.status}"

    class Meta:
        verbose_name = 'Premium Payment'
        verbose_name_plural = 'Premium Payments'


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
    company = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name= 'employees', default= 1)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
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
    company = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name= 'payment_processings', default= 1)
    
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
        
# Agent Report
        
class AgentReport(models.Model):
    agent = models.ForeignKey(SalesAgent, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='agent_reports', default=1)
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
        report.commission_earned += Decimal(instance.amount) * agent.commission_rate / Decimal(100)  # Ensure Decimal
        report.save()


# Underwriting Process Or report

class Underwriting(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='under_writings', default= 1
    )
    policy_holder = models.ForeignKey(
        PolicyHolder, related_name='underwritings', on_delete=models.CASCADE
    )
    policy = models.ForeignKey(
        InsurancePolicy, related_name='underwritings', on_delete=models.CASCADE, null=True, blank=True
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,  
        default="Pending"
    )
    risk_assessment_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    remarks = models.TextField(null=True, blank=True)
    evaluated_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True
    )
    evaluation_date = models.DateField(auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
    
        if not self.policy:
            self.policy = InsurancePolicy.objects.filter(
                policy_holder=self.policy_holder
            ).first()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Underwriting for {self.policy_holder} - {self.status}"

    class Meta:
        verbose_name = 'Underwriting'
        verbose_name_plural = 'Underwritings'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['evaluation_date']),
        ]
