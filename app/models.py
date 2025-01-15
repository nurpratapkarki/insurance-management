from django.db import models
from django.contrib.auth.models import User, AbstractUser
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.utils.timezone import now
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
    RISK_CHOICES,
    PAYMENT_CHOICES
)
import logging

logger = logging.getLogger(__name__)

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
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPES, default='Term')
    base_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    min_sum_assured = models.DecimalField(max_digits=12, decimal_places=2, default=500.00)
    max_sum_assured = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
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
    def clean(self):
        super().clean()
        if self.policy_type == "Term" and self.base_multiplier != 1.0:
            raise ValidationError("Base multiplier for Term insurance must always be 1.0.")


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


#Insurance Policy ends

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

class DurationFactor(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE,)
    min_duration = models.PositiveIntegerField(help_text="Minimum duration in years")
    max_duration = models.PositiveIntegerField(help_text="Maximum duration in years")
    factor = models.DecimalField(max_digits=5, decimal_places=2)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPES)
    
    class Meta:
        unique_together = ['company', 'min_duration', 'max_duration', 'policy_type']
        ordering = ['min_duration']

    def clean(self):
        if self.min_duration >= self.max_duration:
            raise ValidationError("Minimum duration must be less than maximum duration")
        
        # Check for overlapping ranges for same company and policy type
        overlapping = DurationFactor.objects.filter(
            company=self.company,
            policy_type=self.policy_type,
            min_duration__lte=self.max_duration,
            max_duration__gte=self.min_duration
        ).exclude(pk=self.pk)
        
        if overlapping.exists():
            raise ValidationError("Duration ranges cannot overlap for the same company and policy type")

    def __str__(self):
        return f"{self.company} - {self.policy_type} ({self.min_duration}-{self.max_duration} years): {self.factor}x"
    
    
#policy holders start

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
    pan_number = models.CharField(max_length=20, blank=True, null=True)
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
    province = models.CharField(max_length=255, choices=PROVINCE_CHOICES, default='Karnali')
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
    null=True)    
    policy = models.ForeignKey(
        InsurancePolicy, related_name='policy_holders', on_delete=models.CASCADE, blank=True, null=True
    )
    health_history = models.CharField(max_length=500, null=True, blank=True)
    habits = models.CharField(max_length=500, null=True, blank=True)
    exercise_frequency = models.CharField(
        max_length=50,
        choices=EXE_FREQ_CHOICE,
        blank=True,
        null=True
    )
    alcoholic = models.BooleanField(default= False)
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
    start_date = models.DateField(default=date.today)

    maturity_date = models.DateField(null=True, blank=True)
    
    def clean(self):
        """Validate the policy holder data"""
        errors = {}
        
        # Validate sum assured
        if self.sum_assured and self.policy:
            if self.sum_assured < self.policy.min_sum_assured:
                errors['sum_assured'] = f"Sum assured must be at least {self.policy.min_sum_assured}."
            elif self.sum_assured > self.policy.max_sum_assured:
                errors['sum_assured'] = f"Sum assured cannot exceed {self.policy.max_sum_assured}."
        
        # Validate age
        if self.date_of_birth:
            age = self.calculate_age()
            if age < 18 or age > 60:
                errors['date_of_birth'] = f"Age must be between 18 and 60. Current age: {age}."
        
        if errors:
            raise ValidationError(errors)

    def calculate_age(self):
        """Calculate age based on date of birth"""
        if self.date_of_birth:
            today = now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    def calculate_maturity_date(self):
        """Calculate maturity date based on start date and duration"""
        if self.start_date and self.duration_years:
            return self.start_date.replace(year=self.start_date.year + self.duration_years)
        return None

    def generate_policy_number(self):
        """Generate a unique policy number"""
        if not self.company or not self.branch:
            return None
            
        try:
            last_holder = PolicyHolder.objects.filter(
                company=self.company,
                branch=self.branch
            ).exclude(policy_number__isnull=True).order_by('-policy_number').first()
            
            if last_holder and last_holder.policy_number:
                # Extract the numeric part
                last_number = int(last_holder.policy_number[-5:])
            else:
                last_number = 0
                
            new_number = last_number + 1
            return f"{self.company.company_code}{self.branch.branch_code}{str(new_number).zfill(5)}"
        except (ValueError, AttributeError):
            return None

    def save(self, *args, **kwargs):
        """Override save method to handle automatic field updates"""
        # Calculate age if date of birth is provided
        if self.date_of_birth:
            self.age = self.calculate_age()
        
        # Generate policy number if status is Active and number doesn't exist
        if self.status == 'Active' and not self.policy_number:
            self.policy_number = self.generate_policy_number()
        
        # Set maturity date if not already set
        if not self.maturity_date:
            self.maturity_date = self.calculate_maturity_date()
        
        # Run full validation
        self.full_clean()
        
        super().save(*args, **kwargs)

    def __str__(self):
        """String representation of the policy holder"""
        policy_num = self.policy_number if self.policy_number else 'Pending'
        return f"{self.first_name} {self.last_name} ({policy_num})"

    class Meta:
        indexes = [
            models.Index(fields=['company', 'branch']),
            models.Index(fields=['policy']),
        ]        
#policy holders end



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
        try:
            self.risk_assessment_score = self.calculate_risk()
            self.risk_category = self.determine_risk_category()
        except ValidationError as e:
            raise ValidationError(f"Error calculating risk: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error during risk calculation: {e}")
        super().save(*args, **kwargs)


    def calculate_risk(self):
        """Calculate risk score based on age and occupation."""
        age = self.policy_holder.age
        if age is None:
            raise ValidationError("PolicyHolder's age is not set. Ensure the date of birth is provided.")
    
        occupation_risk = {
            'Low': 10,
            'Moderate': 20,
            'High': 30,
        }.get(self.policy_holder.occupation.risk_category, 20)  # Default to Moderate risk if undefined

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
    annual_premium = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    interval_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Amount to be added
    next_payment_date = models.DateField(null=True, blank=True)
    fine_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_premium = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    remaining_premium = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    payment_status = models.CharField(max_length=255, choices=PAYMENT_CHOICES, default='Unpaid')
    
    def calculate_premium(self):
        """Calculate total and interval premiums with company-specific duration factors."""
        policy = self.policy_holder.policy
        sum_assured = self.policy_holder.sum_assured
        duration_years = self.policy_holder.duration_years

        if not sum_assured or not policy:
            raise ValidationError("Sum assured and insurance policy are required.")

        # Get mortality rate
        mortality_rate = self.get_mortality_rate()
        base_premium = (sum_assured * Decimal(mortality_rate)) / Decimal(1000)

        # Get company-specific duration factor
        duration_factor = self.get_duration_factor()

        # Apply policy type multiplier and duration factor
        if policy.policy_type == "Endowment":
            adjusted_premium = base_premium * policy.base_multiplier * duration_factor
        else:
            # Term insurance - always uses base premium
            adjusted_premium = base_premium

        # Calculate add-on charges based on sum assured
        adb_charge = Decimal('0.00')
        if policy.include_adb:
            adb_charge = (sum_assured * Decimal(policy.adb_percentage)) / Decimal(100)

        ptd_charge = Decimal('0.00')
        if policy.include_ptd:
            ptd_charge = (sum_assured * Decimal(policy.ptd_percentage)) / Decimal(100)

        # Total annual premium including all charges
        annual_premium = adjusted_premium + adb_charge + ptd_charge

        # Calculate interval payment based on payment frequency
        interval_mapping = {
            "quarterly": 4,
            "semi_annual": 2,
            "annual": 1,
            "Single": 1,
        }
        interval_count = interval_mapping.get(self.policy_holder.payment_interval, 1)

        if self.policy_holder.payment_interval == "Single":
            # For single payment, calculate the total needed for the entire duration
            # You might want to add a discount for single payment if needed
            # single_payment_discount = Decimal('0.90')  # 10% discount example
            total_premium = annual_premium * Decimal(duration_years)
            interval_payment = total_premium
        else:
            interval_payment = annual_premium / Decimal(interval_count)

        # Round to 2 decimal places
        annual_premium = annual_premium.quantize(Decimal('1.00'), rounding=ROUND_HALF_UP)
        interval_payment = interval_payment.quantize(Decimal('1.00'), rounding=ROUND_HALF_UP)
        return annual_premium, interval_payment

    def get_duration_factor(self):
        """Get appropriate duration factor based on policy duration"""
        duration_years = self.policy_holder.duration_years
        policy_type = self.policy_holder.policy.policy_type
        
        try:
            factor = DurationFactor.objects.get(
                company=self.policy_holder.company,
                policy_type=policy_type,
                min_duration__lte=duration_years,
                max_duration__gte=duration_years
            )
            return factor.factor
        except DurationFactor.DoesNotExist:
            # Log that no duration factor was found
            logger.warning(
                f"No duration factor found for company {self.policy_holder.company.id}, "
                f"policy type {policy_type}, duration {duration_years} years. Using default factor."
            )
            return Decimal('1.0')  # Default factor if no range defined

    def save(self, *args, **kwargs):
        if not self.pk:  # New instance
            self.annual_premium, self.interval_payment = self.calculate_premium()

            if self.policy_holder.payment_interval == "Single":
                self.total_premium = self.interval_payment
            else:
                self.total_premium = self.annual_premium * Decimal(str(self.policy_holder.duration_years))

        # Convert paid_amount to Decimal if it's not already
        if isinstance(self.paid_amount, float):
            self.paid_amount = Decimal(str(self.paid_amount))
    
        # Handle new payment if paid_amount is provided
        if self.paid_amount > 0:
            if isinstance(self.total_paid, float):
                self.total_paid = Decimal(str(self.total_paid))
            self.total_paid += self.paid_amount
            self.paid_amount = Decimal('0.00')  # Reset paid_amount after adding to total_paid
        
        # Update remaining premium and payment status
        self.remaining_premium = max(self.total_premium - self.total_paid, Decimal('0.00'))
    
        if self.total_paid >= self.total_premium:
            self.payment_status = 'Paid'
        elif self.total_paid > 0:
            self.payment_status = 'Partially Paid'
        else:
            self.payment_status = 'Unpaid'

        # Handle fine
        if self.fine_due > 0:
            if isinstance(self.fine_due, float):
                self.fine_due = Decimal(str(self.fine_due))
            if isinstance(self.interval_payment, float):
                self.interval_payment = Decimal(str(self.interval_payment))
                self.interval_payment += self.fine_due
                self.fine_due = Decimal('0.00')

        # Set next payment date
        if not self.next_payment_date and self.policy_holder.payment_interval != "Single":
            interval_months = {
                "quarterly": 3,
                "semi_annual": 6,
                "annual": 12
            }.get(self.policy_holder.payment_interval)

            if interval_months:
                today = date.today()
                self.next_payment_date = today.replace(
                    month=((today.month - 1 + interval_months) % 12) + 1,
                    year=today.year + ((today.month - 1 + interval_months) // 12)
            )

        super().save(*args, **kwargs)

    def get_mortality_rate(self):
        """Fetch mortality rate for the policyholder."""
        age = self.policy_holder.age
        company = self.policy_holder.company

        try:
            mortality_rate = MortalityRate.objects.get(
                company=company,
                age_group_start__lte=age,
                age_group_end__gte=age
            )
            return mortality_rate.rate
        except MortalityRate.DoesNotExist:
            raise ValidationError(f"No mortality rate found for age {age}.")

    class Meta:
        verbose_name = "Premium Payment"
        verbose_name_plural = "Premium Payments"

    def __str__(self):
        return f"Premium Payment - {self.policy_holder.first_name} {self.policy_holder.last_name} ({self.payment_status})"

        
        
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
