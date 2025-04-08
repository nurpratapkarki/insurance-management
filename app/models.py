from django.db import models
from django.contrib.auth.models import User, AbstractUser
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.db.models import Sum
from django.db.models import Sum, Avg, Count, F
from typing import Dict, Union
from django.dispatch import receiver
import logging
from django.utils import timezone
import random


logger = logging.getLogger(__name__)
from .constants import (
    GENDER_CHOICES,
    POLICY_TYPES,
    DOCUMENT_TYPES,
    PROVINCE_CHOICES,
    REASON_CHOICES,
    STATUS_CHOICES,
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
        return f"{self.name} ({self.risk_category})"
    
class MortalityRate(models.Model):
    
    age_group_start = models.PositiveIntegerField(null = True, blank= True)
    age_group_end = models.PositiveIntegerField(null = True, blank= True)
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, null = True, blank= True)

    class Meta:
        unique_together = ( 'age_group_start', 'age_group_end')

    def __str__(self):
        return f"{self.age_group_start}-{self.age_group_end}: {self.rate}%"

class Company(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    company_code = models.IntegerField(unique=True, default=1)
    address = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company', null=True, blank=True)
    email = models.EmailField(max_length=255)
    is_active = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

class Branch(models.Model):
    name = models.CharField(max_length=255)
    branch_code = models.IntegerField(unique=True, default=1)
    location = models.CharField(max_length=255, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches', default=1)

    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'

    def __str__(self):
        return f"{self.name} ({self.branch_code})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='employees'
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        if self.branch and not self.company:
            self.company = self.branch.company
        super().save(*args, **kwargs)

# Basic Information about Insurance Policies

class InsurancePolicy(models.Model):
    name = models.CharField(max_length=200)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPES, default='Term')
    base_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    min_sum_assured = models.DecimalField(max_digits=12, decimal_places=2, default=500.00)
    max_sum_assured = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    include_adb = models.BooleanField(default=False)
    include_ptd = models.BooleanField(default=False)
    adb_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # ADB charge %
    ptd_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # PTD charge %
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.policy_type})"

    class Meta:
        verbose_name = "Insurance Policy"
        verbose_name_plural = "Insurance Policies"
    def clean(self):
        super().clean()
        if self.policy_type == "Term" and self.base_multiplier != 1.0:
            raise ValidationError("Base multiplier for Term insurance must always be 1.0.")
        if self.min_sum_assured > self.max_sum_assured:
            raise ValidationError("Minimum sum assured cannot be greater than maximum sum assured")
        if self.include_adb and self.adb_percentage <= 0:
            raise ValidationError("ADB percentage must be greater than 0 when ADB is included")
        if self.include_ptd and self.ptd_percentage <= 0:
            raise ValidationError("PTD percentage must be greater than 0 when PTD is included")
#Guranteed Surrender Value
class GSVRate(models.Model):
    policy = models.ForeignKey('InsurancePolicy', on_delete=models.CASCADE, related_name='gsv_rates')
    min_year = models.PositiveIntegerField(help_text="Minimum year of the range.")
    max_year = models.PositiveIntegerField(help_text="Maximum year of the range.")
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="GSV rate as a percentage.")

    def clean(self):
        """Ensure the year range is valid and does not overlap with other GSV ranges."""
        if self.min_year > self.max_year:
            raise ValidationError("Minimum year cannot be greater than maximum year")
        if self.rate < 0:
            raise ValidationError("Rate cannot be negative")
        if self.rate > 100:
            raise ValidationError("Rate cannot be greater than 100%")

    

        # Get all existing ranges for the policy
        existing_ranges = GSVRate.objects.filter(
            policy=self.policy
        ).exclude(pk=self.pk)  # Exclude the current instance


        # Check for overlaps using strict inequality for ranges
        overlapping = existing_ranges.filter(
            models.Q(
                # New range starts strictly before existing range ends
                min_year__lt=self.max_year,
                # AND existing range ends strictly after new range starts
                max_year__gt=self.min_year
            )
        )

        if overlapping.exists():
            raise ValidationError("GSV year ranges cannot overlap for the same policy.")

    def __str__(self):
        return f"{self.policy.name} - {self.min_year}-{self.max_year} years ({self.rate}%)"

# SSv Factor
class SSVConfig(models.Model):
    policy = models.ForeignKey('InsurancePolicy', on_delete=models.CASCADE, related_name='ssv_configs')
    min_year = models.PositiveIntegerField(help_text="Minimum year of the range.")
    max_year = models.PositiveIntegerField(help_text="Maximum year of the range.")
    ssv_factor = models.DecimalField(max_digits=5, decimal_places=2, help_text="SSV factor as a percentage.")
    eligibility_years = models.PositiveIntegerField(default=5, help_text="Years of premium payment required for SSV eligibility.")
    custom_condition = models.TextField(blank=True, help_text="Optional custom condition for SSV.")

    def clean(self):
        """Ensure the year range is valid and does not overlap with other SSV ranges."""
        if self.min_year >= self.max_year:
            raise ValidationError("Minimum year must be less than maximum year.")

        overlapping = SSVConfig.objects.filter(
            policy=self.policy,
            min_year__lte=self.max_year,
            max_year__gte=self.min_year
        ).exclude(pk=self.pk)  # Exclude the current instance

        if overlapping.exists():
            raise ValidationError("SSV year ranges cannot overlap for the same policy.")

    def __str__(self):
        return f"{self.policy.name} - {self.min_year}-{self.max_year} years ({self.ssv_factor}%)"


#  Agent Application

class AgentApplication(models.Model):
    id = models.BigAutoField(primary_key=True)
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
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['status']),
        ]


#Insurance Policy ends

# Sales Agent

class SalesAgent(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, related_name='sales_agent', null=True, blank=True)
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
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=200, null=True, blank=True)
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
            models.Index(fields=['agent_code']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['status']),
        ]
        
class DurationFactor(models.Model):
    min_duration = models.PositiveIntegerField(help_text="Minimum duration in years")
    max_duration = models.PositiveIntegerField(help_text="Maximum duration in years")
    factor = models.DecimalField(max_digits=5, decimal_places=2)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPES)

    class Meta:
        unique_together = ['min_duration', 'max_duration', 'policy_type']
        ordering = ['min_duration']

    def clean(self):
        if self.min_duration >= self.max_duration:
            raise ValidationError("Minimum duration must be less than maximum duration")
        

        overlapping = DurationFactor.objects.filter(
            policy_type=self.policy_type,
            min_duration__lte=self.max_duration,
            max_duration__gte=self.min_duration
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError("Duration ranges cannot overlap for the same policy type")

    def __str__(self):
        return f"{self.policy_type} - {self.min_duration}-{self.max_duration} years ({self.factor})"

#policy holders start

class PolicyHolder(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, related_name='policy_holder', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='policy_holders', default=1)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)
    policy_number = models.IntegerField(
        unique=True, default='', blank=True, null=True)
    agent = models.ForeignKey(SalesAgent, on_delete=models.CASCADE, null=True, blank=True)
    policy = models.ForeignKey(InsurancePolicy, related_name='policy_holders', on_delete=models.CASCADE, blank=True, null=True)
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
        unique=True, 
        null=True, 
        blank=True
    )
    email = models.EmailField(max_length=200, null=True, blank=True)
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    work_environment_risk = models.CharField(
    max_length=50, 
    choices=RISK_CHOICES, 
        blank=True, 
    null=True)    
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
    risk_category = models.CharField(
        max_length=50,
        choices=[('Low', 'Low Risk'), ('Moderate', 'Moderate Risk'), ('High', 'High Risk')],
        default='Moderate',
        blank=True, 
        help_text="Risk category assigned based on underwriting."
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(
        max_length=50, choices=PAYMENT_CHOICES, default="Unpaid")
    start_date = models.DateField(default=date.today)
    maturity_date = models.DateField(null=True, blank=True)
    beema_samiti_reg_number = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Beema Samiti (Insurance Board) registration number"
    )
    citizenship_number = models.CharField(
        max_length=30, 
        blank=True, 
        null=True, 
        help_text="Nepal citizenship number"
    )
    kyc_verified = models.BooleanField(
        default=False,
        help_text="Know Your Customer verification status"
    )
    approval_date = models.DateField(
        blank=True, 
        null=True,
        help_text="Date when policy was approved by regulatory authority"
    )
    tax_status = models.CharField(
        max_length=50,
        choices=[('Exempt', 'Tax Exempt'), ('Taxable', 'Taxable')],
        default='Taxable',
        help_text="Tax status of the policy"
    )

    def clean(self):
        errors = {}
        if self.sum_assured:
            if self.sum_assured < self.policy.min_sum_assured:
                errors['sum_assured'] = f"Sum assured must be at least {self.policy.min_sum_assured}."
        elif self.sum_assured > self.policy.max_sum_assured:
            errors['sum_assured'] = f"Sum assured cannot exceed {self.policy.max_sum_assured}."
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
        if self.start_date and self.duration_years:
            return self.start_date.replace(year=self.start_date.year + self.duration_years)
        return None

    def generate_policy_number(self):
        """Generate a unique policy number."""
        if not self.company or not self.branch:
            return None

        try:
            last_holder = PolicyHolder.objects.filter(
                company=self.company, branch=self.branch
            ).exclude(policy_number__isnull=True).order_by('-policy_number').first()

            last_number = int(str(last_holder.policy_number)[-5:]) if last_holder else 0
            new_number = last_number + 1
            return f"{self.company.company_code}{self.branch.branch_code}{str(new_number).zfill(5)}"
        except Exception as e:
            raise ValueError(f"Error generating policy number: {e}")

    def check_for_maturity(self):
        """Check if policy has reached maturity date"""
        if self.status != 'Active':
            return False
            
        today = date.today()
        if self.maturity_date and today >= self.maturity_date:
            logger.info(f"Policy {self.id} has reached maturity on {self.maturity_date}")
            self.surrender_policy('Maturity')
            return True
        return False
        
    def surrender_policy(self, surrender_type='Voluntary', reason=None):
        """Surrender the policy and create a surrender request"""
        if self.status == 'Surrendered':
            return False
            
        try:
            # Create surrender request
            surrender = PolicySurrender.objects.create(
                policy_holder=self,
                surrender_type=surrender_type,
                surrender_reason=reason
            )
            
            # Auto-approve for maturity surrenders
            if surrender_type == 'Maturity':
                admin_user = User.objects.filter(is_superuser=True).first()
                if admin_user:
                    surrender.approve_surrender(admin_user)
                else:
                    # Mark policy as surrendered even without admin user
                    self.status = 'Surrendered'
                    self.save(update_fields=['status'])
            
            # Auto-approve for automatic surrenders
            if surrender_type == 'Automatic':
                admin_user = User.objects.filter(is_superuser=True).first()
                if admin_user:
                    surrender.approve_surrender(admin_user)
                else:
                    # Mark policy as surrendered even without admin user
                    self.status = 'Surrendered'
                    self.save(update_fields=['status'])
                    
            logger.info(f"Policy {self.id} has been surrendered via {surrender_type}")
            return surrender
            
        except Exception as e:
            logger.error(f"Error surrendering policy {self.id}: {str(e)}")
            return False

    def check_for_renewal(self):
        """Check if policy needs renewal and create renewal record if needed."""
        from datetime import timedelta
        
        # Only check for renewal for annual payment policies that are active
        if self.status != 'Active' or self.payment_interval != 'annual':
            return False
            
        today = date.today()
        
        # Calculate 60 days before maturity as the renewal notification date
        if self.maturity_date:
            renewal_due_date = self.maturity_date - timedelta(days=60)
            
            # If we're within 60 days of maturity and no renewal record exists yet
            if today >= renewal_due_date and not self.renewals.filter(
                due_date=self.maturity_date, 
                status__in=['Pending', 'Renewed']
            ).exists():
                # Get premium amount from premium payment
                premium_payment = self.premium_payments.first()
                renewal_amount = premium_payment.annual_premium if premium_payment else Decimal('0.00')
                
                # Create renewal record
                renewal = PolicyRenewal.objects.create(
                    policy_holder=self,
                    due_date=self.maturity_date,
                    renewal_amount=renewal_amount
                )
                
                # Send first reminder immediately upon creation
                renewal.send_reminder('first')
                
                logger.info(f"Renewal record created for policy {self.policy_number}")
                return renewal
                
        return False
    
    def get_active_renewal(self):
        """Get any active (pending) renewal for this policy."""
        return self.renewals.filter(status='Pending').first()
    
    def renew_policy(self, user):
        """Renew this policy."""
        active_renewal = self.get_active_renewal()
        if active_renewal:
            return active_renewal.mark_as_renewed(user)
        return False

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
        
        # Check for policy maturity
        if self.pk and self.status == 'Active':
            self.check_for_maturity()
            self.check_for_renewal()  # Check for renewal needs
            
        # Run full validation
        self.full_clean()
        
        super().save(*args, **kwargs)

    def __str__(self):
        """String representation of the policy holder"""
        policy_num = self.policy_number if self.policy_number else 'Pending'
        return f"{self.first_name} {self.last_name} ({policy_num})"

    class Meta:
        indexes = [
            models.Index(fields=['branch']),
            models.Index(fields=['policy']),
        ]        
#policy holders end


# Bonus Rate model

class BonusRate(models.Model):
    year = models.PositiveIntegerField(
        default=date.today().year,  # ✅ Default to current year
        help_text="Year the bonus rate applies to"
    )
    policy_type = models.CharField(
        max_length=50,
        choices=POLICY_TYPES, default= 'Term', # Ensure POLICY_TYPES is defined
        help_text="Applicable policy type"
    )
    min_year = models.PositiveIntegerField(help_text="Minimum policy duration in years", default=1)
    max_year = models.PositiveIntegerField(help_text="Maximum policy duration in years" , default=9)
    bonus_per_thousand = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Bonus amount per 1000 of sum assured", default=0.00
    )

    class Meta:
        unique_together = ['policy_type', 'min_year', 'max_year']
        ordering = ['policy_type', 'min_year']

    def __str__(self):
        return f"{self.policy_type}: {self.min_year}-{self.max_year} years -> {self.bonus_per_thousand} per 1000"

    @classmethod
    def get_bonus_rate(cls, policy_type, duration):
        """Fetch the correct bonus rate based on policy type and duration."""
        return cls.objects.filter(
            policy_type=policy_type,
            min_year__lte=duration,
            max_year__gte=duration
        ).first()


#Bonus Model
class BonusHistory(models.Model):
    """Model to track the history of bonus calculations"""
    policy_holder = models.ForeignKey(PolicyHolder, on_delete=models.CASCADE, related_name='bonus_history')
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    calculation_date = models.DateField(auto_now_add=True, help_text="Date this bonus was calculated")
    policy_year = models.PositiveIntegerField(help_text="Policy year this bonus applies to")
    bonus_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Bonus rate per 1000 used for calculation")
    
    def __str__(self):
        return f"Year {self.policy_year} Bonus for {self.policy_holder} - {self.bonus_amount}"
    
    class Meta:
        verbose_name = "Bonus History"
        verbose_name_plural = "Bonus History"
        ordering = ['-calculation_date']
        unique_together = ['policy_holder', 'policy_year']

class Bonus(models.Model):
    policy_holder = models.ForeignKey(PolicyHolder, on_delete=models.CASCADE, related_name='bonuses')
    accrued_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    start_date = models.DateField(help_text="Start date for bonus accrual.")
    last_updated = models.DateField(auto_now=True)
    last_anniversary_processed = models.DateField(null=True, blank=True, help_text="Last policy anniversary date when bonus was added")
    
    def calculate_bonus(self, for_year=None):
        """Calculate yearly bonus based on policy type, duration, and sum assured."""
        try:
            policy = self.policy_holder.policy
            policy_start_date = self.policy_holder.start_date
            sum_assured = self.policy_holder.sum_assured
            today = date.today()
            
            # If for_year is provided, use it; otherwise calculate current policy year
            if for_year is not None:
                policy_year = for_year
            else:
                policy_years = (today.year - policy_start_date.year)
                if policy_years <= 0:
                    return Decimal(0)  # No bonus in first year
                policy_year = policy_years
                
            logger.info(f"BONUS CALCULATION - Starting for policy_holder_id={self.policy_holder.id}, " +
                      f"policy={policy}, sum_assured={sum_assured}, policy_year={policy_year}")
            
            # Only endowment policies get bonuses
            if policy.policy_type != "Endowment":
                logger.info(f"BONUS CALCULATION - No bonus for policy type {policy.policy_type}")
                return Decimal(0)

            # Fetch applicable bonus rate for the current year and policy duration
            bonus_rate_obj = BonusRate.get_bonus_rate(policy.policy_type, policy_year)
            if not bonus_rate_obj:
                logger.warning(f"BONUS CALCULATION - No bonus rate defined for type={policy.policy_type}, year={policy_year}")
                return Decimal(0)  # No bonus if rate is not defined

            bonus_per_1000 = Decimal(bonus_rate_obj.bonus_per_thousand)
            logger.info(f"BONUS CALCULATION - Found bonus rate: {bonus_per_1000} per 1000 for year {policy_year}")
            
            # Calculate bonus amount = (Sum Assured / 1000) * Bonus Rate per 1000
            bonus_amount = (sum_assured / Decimal(1000)) * bonus_per_1000
            bonus_amount = bonus_amount.quantize(Decimal('1.00'))
            
            logger.info(f"BONUS CALCULATION - Calculated bonus amount: {bonus_amount}")
            
            # Record in bonus history if this is a new calculation
            if for_year is None or not BonusHistory.objects.filter(
                policy_holder=self.policy_holder, policy_year=policy_year
            ).exists():
                BonusHistory.objects.create(
                    policy_holder=self.policy_holder,
                    policy_year=policy_year,
                    bonus_amount=bonus_amount,
                    bonus_rate=bonus_per_1000
                )
                logger.info(f"BONUS CALCULATION - Created bonus history record for year {policy_year}")

            return bonus_amount

        except Exception as e:
            logger.error(f"BONUS CALCULATION - Error: {str(e)}")
            raise ValidationError(f"Error calculating bonus: {e}")

    def update_anniversary_bonus(self):
        """Check if policy anniversary has passed and add new bonus if needed."""
        try:
            # Skip if not anniversary month/date
            policy_start = self.policy_holder.start_date
            today = date.today()
            
            # Check if we're in the anniversary month/date
            is_anniversary = (policy_start.month == today.month and policy_start.day == today.day)
            
            if not is_anniversary:
                # Also check if we missed an anniversary (within last 30 days)
                days_since_anniversary = 0
                # Calculate the anniversary date for the current year
                anniversary_this_year = date(today.year, policy_start.month, policy_start.day)
                
                # If the anniversary this year is in the future, use last year's anniversary
                if anniversary_this_year > today:
                    anniversary_this_year = date(today.year - 1, policy_start.month, policy_start.day)
                    
                days_since_anniversary = (today - anniversary_this_year).days
                
                # Only process if we're within 30 days after the anniversary
                if days_since_anniversary > 30:
                    return False
            
            # Check if we already processed this anniversary
            anniversary_year = today.year
            if policy_start.month > today.month or (policy_start.month == today.month and policy_start.day > today.day):
                anniversary_year -= 1
                
            anniversary_date = date(anniversary_year, policy_start.month, policy_start.day)
            
            if self.last_anniversary_processed and self.last_anniversary_processed >= anniversary_date:
                logger.info(f"BONUS UPDATE - Anniversary {anniversary_date} already processed for policy {self.policy_holder.id}")
                return False
                
            # Calculate policy year
            policy_year = anniversary_year - policy_start.year
            
            # Don't add bonus for first year 
            if policy_year <= 0:
                return False
                
            # Calculate and add bonus
            new_bonus = self.calculate_bonus(for_year=policy_year)
            self.accrued_amount += new_bonus
            self.last_anniversary_processed = anniversary_date
            self.save(update_fields=['accrued_amount', 'last_anniversary_processed'])
            
            logger.info(f"BONUS UPDATE - Added anniversary bonus of {new_bonus} for policy {self.policy_holder.id}, year {policy_year}")
            return True
            
        except Exception as e:
            logger.error(f"BONUS UPDATE - Error updating anniversary bonus: {str(e)}")
            return False

    def save(self, *args, **kwargs):
        """Recalculate and save accrued bonus."""
        # For new bonus records, initialize with current value
        if not self.pk:
            # Set start date if not provided
            if not self.start_date:
                self.start_date = self.policy_holder.start_date
                
            # Calculate initial accrued amount from history
            bonus_history = BonusHistory.objects.filter(policy_holder=self.policy_holder)
            self.accrued_amount = bonus_history.aggregate(total=Sum('bonus_amount'))['total'] or Decimal('0.00')
        else:
            # Existing record - check for anniversary
            self.update_anniversary_bonus()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bonus for {self.policy_holder.first_name} {self.policy_holder.last_name} ({self.accrued_amount})"
        
    class Meta:
        verbose_name = "Bonus"
        verbose_name_plural = "Bonuses"
        indexes = [
            models.Index(fields=['policy_holder']),
            models.Index(fields=['last_updated']),
        ]

# claim requestes

class ClaimRequest(models.Model):
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='claim_requests', default=1
    )
    policy_holder = models.ForeignKey(
        PolicyHolder, on_delete=models.CASCADE, related_name='claim_requests'
    )
    claim_date = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    bill = models.ImageField(upload_to='claim_processing', null=True, blank=True)
    policy_copy = models.ImageField(upload_to='claim_processing', null=True, blank=True)
    health_report = models.ImageField(upload_to='claim_processing', null=True, blank=True)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default='Others')
    other_reason = models.CharField(max_length=500, null=True, blank=True)
    claim_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def calculate_claim_amount(self):
        """Calculate the claimable amount."""
        sum_assured = self.policy_holder.sum_assured or Decimal(0)
        outstanding_loans = self.policy_holder.loans.filter(loan_status='Active').aggregate(
            total=Sum('remaining_balance')
        )['total'] or Decimal(0)
        return max(sum_assured - outstanding_loans, Decimal(0))

    def save(self, *args, **kwargs):
        """Auto-calculate claim amount before saving."""
        self.claim_amount = self.calculate_claim_amount()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Claim {self.id} - {self.policy_holder}"

    class Meta:
        verbose_name = "Claim Request"
        verbose_name_plural = "Claim Requests"


# Claim Processing
class ClaimProcessing(models.Model):
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='claim_processings', default=1
    )
    claim_request = models.OneToOneField(
        ClaimRequest, on_delete=models.CASCADE, related_name='processing'
    )
    processing_status = models.CharField(
        max_length=50,
        choices=[('In Progress', 'In Progress'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='In Progress'
    )
    remarks = models.TextField(null=True, blank=True)
    processing_date = models.DateField(auto_now=True)

    def finalize_claim(self):
        """Finalize claim based on approval."""
        if self.processing_status == 'Approved':
            PaymentProcessing.objects.create(
                branch=self.branch,
                name=f"Claim Settlement - {self.claim_request.policy_holder}",
                claim_request=self.claim_request,
                processing_status='Completed',
            )
            self.claim_request.status = 'Approved'
        elif self.processing_status == 'Rejected':
            self.claim_request.status = 'Rejected'

        self.claim_request.save()

    def save(self, *args, **kwargs):
        """Finalize claim on save."""
        super().save(*args, **kwargs)
        self.finalize_claim()

    def __str__(self):
        return f"Processing {self.id} - {self.processing_status}"

    class Meta:
        verbose_name = "Claim Processing"
        verbose_name_plural = "Claim Processings"

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
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='payment_processings', default=1
    )
    name = models.CharField(max_length=200)
    processing_status = models.CharField(
        max_length=50,
        choices=[('Pending', 'Pending'), ('Completed', 'Completed')],
        default='Pending'
    )
    claim_request = models.OneToOneField(
        ClaimRequest, on_delete=models.CASCADE, related_name='payment', null=True, blank=True
    )
    date_of_processing = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Payment Processing"
        verbose_name_plural = "Payment Processings"

# Underwriting Process Or report
class Underwriting(models.Model):
    policy_holder = models.OneToOneField(
        'PolicyHolder',
        on_delete=models.CASCADE,
        related_name='underwriting'
    )
    risk_assessment_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="Calculated risk score (0-100)."
    )
    risk_category = models.CharField(
        max_length=50,
        choices=[('Low', 'Low Risk'), ('Moderate', 'Moderate Risk'), ('High', 'High Risk')],
        default='Moderate'
    )
    manual_override = models.BooleanField(
        default=False,
        help_text="Enable to manually update risk scores."
    )
    premium_loading_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="Additional premium percentage based on risk assessment."
    )
    underwriting_date = models.DateField(
        default=date.today,
        help_text="Date of initial underwriting."
    )
    last_reviewed_date = models.DateField(
        null=True, blank=True,
        help_text="Date of last underwriting review."
    )
    needs_review = models.BooleanField(
        default=False,
        help_text="Flag indicating this policy needs underwriting review."
    )
    medical_examination_required = models.BooleanField(
        default=False,
        help_text="Indicates if a medical examination is required."
    )
    medical_examination_completed = models.BooleanField(
        default=False,
        help_text="Indicates if required medical examination was completed."
    )
    additional_documents_required = models.TextField(
        null=True, blank=True,
        help_text="List of additional documents required for underwriting."
    )
    remarks = models.TextField(
        null=True, blank=True, help_text="Additional remarks about underwriting."
    )
    last_updated_by = models.CharField(
        max_length=50,
        choices=[('System', 'System'), ('Admin', 'Admin')],
        default='System'
    )
    last_updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Only calculate risk if manual override is disabled
        if not self.manual_override:
            self.calculate_risk()
            self.last_updated_by = 'System'
        else:
            self.last_updated_by = 'Admin'
        
        # Mark policy for review if high risk or special conditions
        self.check_if_review_needed()
        
        # Set last reviewed date if this is a review
        if self.pk and self.needs_review:
            self.last_reviewed_date = date.today()
            self.needs_review = False
            
        super().save(*args, **kwargs)
        
        # Update policy holder risk category to match
        if self.policy_holder.risk_category != self.risk_category:
            self.policy_holder.risk_category = self.risk_category
            self.policy_holder.save(update_fields=['risk_category'])
        
        # Recalculate premium if needed
        self.update_premium_loading()

    def calculate_risk(self):
        """Automatically calculate the risk score based on policyholder data."""
        try:
            policy_holder = self.policy_holder
            age = policy_holder.age or 0
            
            # Base risk factors
            risk_factors = {
                'age': 0,
                'occupation': 0,
                'health': 0,
                'lifestyle': 0,
                'medical_history': 0,
                'family_history': 0,
                'location': 0,
                'sum_assured': 0
            }
            
            # Age-based risk (0-25 points)
            if age < 30:
                risk_factors['age'] = 5
            elif age <= 40:
                risk_factors['age'] = 10
            elif age <= 50:
                risk_factors['age'] = 15
            elif age <= 60:
                risk_factors['age'] = 20
            else:
                risk_factors['age'] = 25
                
            # Occupation risk (0-20 points)
            if policy_holder.occupation:
                if policy_holder.occupation.risk_category == 'Low':
                    risk_factors['occupation'] = 5
                elif policy_holder.occupation.risk_category == 'Moderate':
                    risk_factors['occupation'] = 10
                elif policy_holder.occupation.risk_category == 'High':
                    risk_factors['occupation'] = 20
            
            # Health risks (0-30 points)
            health_risk = 0
            if policy_holder.smoker:
                health_risk += 15
            if policy_holder.alcoholic:
                health_risk += 10
                
            # Exercise frequency (deduct up to 5 points)
            if policy_holder.exercise_frequency == 'Daily':
                health_risk -= 5
            elif policy_holder.exercise_frequency == 'Several times a week':
                health_risk -= 3
            elif policy_holder.exercise_frequency == 'Once a week':
                health_risk -= 1
                
            risk_factors['health'] = max(0, min(30, health_risk))
            
            # Lifestyle risk factors (0-10 points)
            if policy_holder.work_environment_risk == 'High':
                risk_factors['lifestyle'] += 10
            elif policy_holder.work_environment_risk == 'Moderate':
                risk_factors['lifestyle'] += 5
                
            # Medical history (0-15 points)
            if policy_holder.health_history and len(policy_holder.health_history) > 0:
                risk_factors['medical_history'] = 15
                
            # Family medical history (0-10 points)
            if policy_holder.family_medical_history and len(policy_holder.family_medical_history) > 0:
                risk_factors['family_history'] = 10
                
            # Location based risk (natural hazards) (0-5 points)
            if policy_holder.natural_hazard_exposure == 'High':
                risk_factors['location'] = 5
            elif policy_holder.natural_hazard_exposure == 'Moderate':
                risk_factors['location'] = 3
                
            # Sum assured risk (0-10 points based on policy size)
            if policy_holder.sum_assured and policy_holder.policy:
                sum_assured_ratio = policy_holder.sum_assured / policy_holder.policy.max_sum_assured
                if sum_assured_ratio > 0.8:
                    risk_factors['sum_assured'] = 10
                elif sum_assured_ratio > 0.6:
                    risk_factors['sum_assured'] = 7
                elif sum_assured_ratio > 0.4:
                    risk_factors['sum_assured'] = 4
                elif sum_assured_ratio > 0.2:
                    risk_factors['sum_assured'] = 2
            
            # Calculate total risk score (max 100)
            total_risk = sum(risk_factors.values())
            self.risk_assessment_score = min(total_risk, 100)
            
            # Determine risk category
            self.risk_category = self.determine_risk_category()
            
            # Calculate premium loading based on risk
            self.calculate_premium_loading()
            
            # Set medical examination requirement
            self.medical_examination_required = (self.risk_assessment_score > 65 or age > 50)
            
            # Log the risk assessment process
            logger.info(f"Underwriting risk assessment for policy_holder_id={policy_holder.id}: " +
                      f"score={self.risk_assessment_score}, category={self.risk_category}, " +
                      f"factors={risk_factors}")
                
        except Exception as e:
            logger.error(f"Error calculating underwriting risk: {str(e)}")
            raise ValidationError(f"Error calculating risk: {str(e)}")

    def determine_risk_category(self):
        """Determine risk category based on risk score."""
        score = self.risk_assessment_score
        if score < 30:
            return 'Low'
        elif score < 60:
            return 'Moderate'
        else:
            return 'High'
            
    def calculate_premium_loading(self):
        """Calculate premium loading percentage based on risk score."""
        score = self.risk_assessment_score
        
        # No loading for low risk
        if score < 30:
            self.premium_loading_percentage = Decimal('0.00')
        # 5-10% loading for moderate risk
        elif score < 60:
            self.premium_loading_percentage = Decimal('5.00') + ((score - 30) / 30) * Decimal('5.00')
        # 10-25% loading for high risk
        else:
            self.premium_loading_percentage = Decimal('10.00') + ((score - 60) / 40) * Decimal('15.00')
            
        # Round to nearest 0.5%
        self.premium_loading_percentage = (self.premium_loading_percentage * 2).quantize(Decimal('1.0')) / 2
            
    def update_premium_loading(self):
        """Update premium calculations if loading has changed."""
        try:
            # Get the primary premium payment record
            premium_payment = self.policy_holder.premium_payments.first()
            
            if premium_payment:
                premium_payment.save()  # Trigger recalculation
                logger.info(f"Updated premium for policy_holder_id={self.policy_holder.id} with loading {self.premium_loading_percentage}%")
        except Exception as e:
            logger.error(f"Error updating premium with loading: {str(e)}")
            
    def check_if_review_needed(self):
        """Determine if this policy needs an underwriting review."""
        # Always review high risk policies
        if self.risk_category == 'High':
            self.needs_review = True
            return
            
        # Review if medical exam is required but not completed
        if self.medical_examination_required and not self.medical_examination_completed:
            self.needs_review = True
            return
            
        # Check if it's time for periodic review (policy anniversary)
        if self.last_reviewed_date:
            today = date.today()
            years_since_review = today.year - self.last_reviewed_date.year
            
            # Check if it's been at least a year since last review
            if years_since_review >= 1:
                # And it's within a month of the anniversary
                if abs((today.month - self.last_reviewed_date.month)) <= 1:
                    self.needs_review = True
                    return
                    
        # No review needed
        self.needs_review = False

    def __str__(self):
        return f"Underwriting for {self.policy_holder} ({self.risk_category})"
        
    class Meta:
        verbose_name = "Underwriting"
        verbose_name_plural = "Underwritings"
        indexes = [
            models.Index(fields=['risk_category']),
            models.Index(fields=['needs_review']),
        ]

# Premium Payment Model

class PremiumPayment(models.Model):
    """Model to track premium payments for a policy holder."""
    policy_holder = models.ForeignKey(
        PolicyHolder, 
        on_delete=models.CASCADE, 
        related_name='premium_payments'
    )
    annual_premium = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="Annual premium amount"
    )
    interval_payment = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="Payment amount per interval (e.g. monthly, quarterly)"
    )
    total_premium = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00, 
        help_text="Total premium for the policy duration"
    )
    total_paid = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00, 
        help_text="Total amount paid so far"
    )
    remaining_premium = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00, 
        help_text="Remaining premium to be paid"
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=[
            ('Unpaid', 'Unpaid'), 
            ('Partially Paid', 'Partially Paid'), 
            ('Paid', 'Paid'),
            ('Overdue', 'Overdue'),
        ], 
        default='Unpaid'
    )
    next_payment_date = models.DateField(
        null=True, 
        blank=True, 
        help_text="Due date for the next payment"
    )
    paid_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="Amount being paid in this transaction"
    )
    fine_due = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="Late payment fine due"
    )
    fine_paid = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="Late payment fine paid"
    )
    gsv_value = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="Guaranteed Surrender Value"
    )
    ssv_value = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="Special Surrender Value"
    )
    # New Nepal tax and payment tracking fields
    payment_date = models.DateField(
        auto_now_add=True,
        help_text="Date when the payment was made",
        null=True,
        blank=True
    )
    vat_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="VAT amount (13% in Nepal)"
    )
    service_tax = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="Insurance service tax"
    )
    tds_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        help_text="TDS (Tax Deducted at Source) if applicable"
    )
    receipt_number = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Receipt number for this payment"
    )
    
    def calculate_premium(self):
        """Calculate total and interval premiums for the policy."""
        try:
            policy = self.policy_holder.policy
            sum_assured = self.policy_holder.sum_assured
            duration_years = self.policy_holder.duration_years
            age = self.policy_holder.age  # Ensure this field exists in PolicyHolder

            logger.info(f"PREMIUM CALCULATION - Starting for policy_holder_id={self.policy_holder.id}, " +
                       f"policy={policy}, sum_assured={sum_assured}, age={age}, duration={duration_years}")

            if not policy or not sum_assured or not age:
                logger.error(f"PREMIUM CALCULATION - Missing required data: policy={policy}, " +
                           f"sum_assured={sum_assured}, age={age}")
                raise ValidationError("Policy, Sum Assured, and Age are required for premium calculation.")

            # Fetch mortality rate based on age range
            mortality_rate_obj = MortalityRate.objects.filter(
                age_group_start__lte=age,  
                age_group_end__gte=age  
            ).first()

            if not mortality_rate_obj:
                logger.error(f"PREMIUM CALCULATION - No mortality rate found for age {age}")
                return Decimal('0.00'), Decimal('0.00')  # Instead of returning None

            mortality_rate = Decimal(mortality_rate_obj.rate)
            logger.info(f"PREMIUM CALCULATION - Found mortality rate: {mortality_rate} for age {age}")

            # Base premium calculation
            base_premium = (sum_assured * mortality_rate) / Decimal(1000)
            logger.info(f"PREMIUM CALCULATION - Base premium: {base_premium}")

            # Fetch duration factor
            duration_factor_obj = DurationFactor.objects.filter(
                min_duration__lte=duration_years,  
                max_duration__gte=duration_years,
                policy_type=policy.policy_type
            ).first()

            if not duration_factor_obj:
                logger.error(f"PREMIUM CALCULATION - No duration factor found for duration {duration_years} and policy type {policy.policy_type}")
                return Decimal('0.00'), Decimal('0.00') 

            duration_factor = Decimal(duration_factor_obj.factor)  
            logger.info(f"PREMIUM CALCULATION - Found duration factor: {duration_factor}")

            # Adjust premium based on policy type
            if policy.policy_type == "Endownment":
                adjusted_premium = base_premium * Decimal(policy.base_multiplier) * duration_factor
                logger.info(f"PREMIUM CALCULATION - Endowment premium: {adjusted_premium} (base * {policy.base_multiplier} * {duration_factor})")
            elif policy.policy_type == "Term":
                adjusted_premium = base_premium
                logger.info(f"PREMIUM CALCULATION - Term premium: {adjusted_premium}")
            else:
                logger.error(f"PREMIUM CALCULATION - Unsupported policy type: {policy.policy_type}")
                raise ValidationError(f"Unsupported policy type: {policy.policy_type}")

            # Add ADB/PTD charges if applicable
            adb_charge = (sum_assured * Decimal(policy.adb_percentage)) / Decimal(100) if policy.include_adb else Decimal('0.00')
            ptd_charge = (sum_assured * Decimal(policy.ptd_percentage)) / Decimal(100) if policy.include_ptd else Decimal('0.00')
            logger.info(f"PREMIUM CALCULATION - ADB charge: {adb_charge}, PTD charge: {ptd_charge}")

            # Apply underwriting loading if available
            premium_loading = Decimal('0.00')
            try:
                if hasattr(self.policy_holder, 'underwriting'):
                    underwriting = self.policy_holder.underwriting
                    if underwriting.premium_loading_percentage > 0:
                        premium_loading = (adjusted_premium * underwriting.premium_loading_percentage) / Decimal('100.00')
                        logger.info(f"PREMIUM CALCULATION - Applied underwriting loading: {underwriting.premium_loading_percentage}% = {premium_loading}")
            except Exception as e:
                logger.warning(f"PREMIUM CALCULATION - Error applying underwriting loading: {str(e)}")

            # Calculate final premium with all adjustments
            annual_premium = adjusted_premium + adb_charge + ptd_charge + premium_loading
            logger.info(f"PREMIUM CALCULATION - Annual premium (with loading): {annual_premium}")

            # Calculate interval payments
            interval_mapping = {"quarterly": 4, "semi_annual": 2, "annual": 1, "Single": 1}
            interval_count = interval_mapping.get(self.policy_holder.payment_interval, 1)
            interval_payment = annual_premium / Decimal(interval_count)
            logger.info(f"PREMIUM CALCULATION - Interval payment: {interval_payment} (Annual / {interval_count})")

            annual_premium = annual_premium.quantize(Decimal('1.00'))
            interval_payment = interval_payment.quantize(Decimal('1.00'))
            
            logger.info(f"PREMIUM CALCULATION - RESULT: annual={annual_premium}, interval={interval_payment}")
            return annual_premium, interval_payment

        except ValidationError as e:
            logger.error(f"PREMIUM CALCULATION - Validation error: {e}")
            raise

        except Exception as e:
            logger.error(f"PREMIUM CALCULATION - Unexpected error: {str(e)}")
            return Decimal('0.00'), Decimal('0.00')
    
    # New method for tax calculation
    def calculate_taxes(self):
        """Calculate tax amounts based on Nepal regulations"""
        # VAT calculation (13%)
        self.vat_amount = round(self.paid_amount * Decimal('0.13'), 2)
        
        # Service tax (1% for insurance in Nepal)
        self.service_tax = round(self.paid_amount * Decimal('0.01'), 2)
        
        # TDS calculation (if applicable, usually 15% for agent commission)
        if self.policy_holder.agent:
            # Calculate commission amount (typically 15-25% of premium in Nepal)
            commission_rate = getattr(self.policy_holder.agent, 'commission_rate', Decimal('15'))
            commission_amount = (self.paid_amount * commission_rate) / Decimal('100')
            self.tds_amount = round(commission_amount * Decimal('0.15'), 2)
            
        return self.vat_amount + self.service_tax + self.tds_amount
    
    def add_payment(self, amount):
        """Record a premium payment."""
        # Check if policy is surrendered
        if self.policy_holder.status == 'Surrendered':
            raise ValidationError("Cannot add payment to a surrendered policy.")
        
        # Convert to Decimal for safe operations
        amount = Decimal(str(amount))
        
        # Check for valid amount
        if amount <= 0:
            raise ValidationError("Payment amount must be greater than zero.")
        
        # Get the expected amount (current interval payment)
        expected_amount = self.interval_payment
        
        # Check if there are outstanding fines from previous periods
        has_fine = self.fine_due > Decimal('0.00')
        
        # Handle payment cases
        if amount < expected_amount:
            # Partial payment not accepted for regular premiums
            raise ValidationError(f"Payment amount ({amount}) is less than the required premium ({expected_amount}). Please pay at least the full premium amount.")
        
        # Check for overpayment of total premium
        remaining_for_total = self.total_premium - self.total_paid
        if amount > remaining_for_total and remaining_for_total > 0:
            raise ValidationError(f"Payment amount ({amount}) exceeds the remaining total premium ({remaining_for_total}). Please pay only the remaining amount.")
        
        # Check if already fully paid
        if self.total_paid >= self.total_premium:
            raise ValidationError("This policy is already fully paid. No additional payments are required.")
        
        # Check for already paid periods
        if self.is_current_period_paid():
            if has_fine:
                # Allow payment just for the fine
                if amount > self.fine_due:
                    raise ValidationError(f"You have a fine of {self.fine_due} due. Please pay exactly this amount.")
                # Accept fine payment
                self.fine_paid += amount
                self.fine_due = Decimal('0.00')
                self.paid_amount = amount
                self.save()
                return True
            else:
                raise ValidationError("The current payment period has already been paid. Please wait until the next payment is due.")
        
        # Ensure all values are Decimal for safe operations
        if isinstance(self.paid_amount, float):
            self.paid_amount = Decimal(str(self.paid_amount))
        if isinstance(self.total_paid, float):
            self.total_paid = Decimal(str(self.total_paid))
        
        # Set the paid amount
        self.paid_amount = amount
        
        # Record any unpaid fine to be added to the next payment
        if has_fine and amount == expected_amount:
            # Just pay the premium and leave the fine for next period
            logger.info(f"Fine of {self.fine_due} will be carried over to next payment period")
        elif has_fine and amount > expected_amount:
            # Pay premium and part/all of the fine
            fine_payment = min(amount - expected_amount, self.fine_due)
            self.fine_paid += fine_payment
            self.fine_due -= fine_payment
            logger.info(f"Payment includes fine of {fine_payment}. Remaining fine: {self.fine_due}")
        
        # Update next payment date and include any remaining fine
        self.update_next_payment_date()
        
        self.save()
        
        return True

    def update_next_payment_date(self):
        """Update the next payment date based on the payment interval"""
        if self.policy_holder.payment_interval == "Single":
            # No next payment date for single payment policies
            return
        
        interval_months = {
            "quarterly": 3,
            "semi_annual": 6,
            "annual": 12
        }.get(self.policy_holder.payment_interval)
        
        if not interval_months:
            return
        
        if self.next_payment_date:
            # Calculate next payment date from the current one
            self.next_payment_date = self.next_payment_date.replace(
                month=((self.next_payment_date.month - 1 + interval_months) % 12) + 1,
                year=self.next_payment_date.year + ((self.next_payment_date.month - 1 + interval_months) // 12)
            )
        else:
            # If there's no next payment date, calculate from today
            today = date.today()
            self.next_payment_date = today.replace(
                month=((today.month - 1 + interval_months) % 12) + 1,
                year=today.year + ((today.month - 1 + interval_months) // 12)
            )
    
    def calculate_gsv(self):
        """Calculate Guaranteed Surrender Value (GSV)."""
        try:
            if not self.policy_holder or not self.policy_holder.policy:
                return Decimal(0.00)
    
            gsv_rate = self.policy_holder.policy.gsv_rates.filter(
                min_year__lte=self.policy_holder.duration_years,
                max_year__gte=self.policy_holder.duration_years
            ).first()
    
            if not gsv_rate:
                return Decimal(0.00)
    
            gsv = (self.policy_holder.sum_assured * gsv_rate.rate / 100).quantize(Decimal('0.01'))
            return gsv
        except Exception as e:
            logger.error(f"Error calculating GSV: {e}")
            return Decimal(0.00)
    def calculate_ssv(self):
        """Calculate Special Surrender Value (SSV)."""
        if self.policy_holder.policy.policy_type != "Endowment":
            return Decimal(0)  # SSV only applies to endowment policie
        else:    
            try:
                duration_years = (date.today() - self.policy_holder.start_date).days // 365
                premiums_paid = self.policy_holder.premium_payments.count()

                # Get applicable SSV configuration
                applicable_range = self.policy_holder.policy.ssv_configs.filter(
                    min_year__lte=duration_years, max_year__gte=duration_years
                ).first()

                if not applicable_range or premiums_paid < applicable_range.eligibility_years:
                    return Decimal('0.00')

                # Total Bonuses
                total_bonuses = self.policy_holder.bonuses.aggregate(
                    total=Sum('accrued_amount'))['total'] or Decimal('0.00')
                
                # Calculate SSV
                premium_component = self.total_paid * (applicable_range.ssv_factor / Decimal(100))
                ssv = premium_component + total_bonuses

                return ssv.quantize(Decimal('1.00'))
            except Exception as e:
                raise ValidationError(f"Error calculating SSV: {e}")

    def calculate_fine(self):
        """Calculate late payment fine if applicable"""
        if not self.next_payment_date:
            return Decimal('0.00')
            
        today = date.today()
        if today <= self.next_payment_date:
            return Decimal('0.00')
            
        # Calculate days late
        days_late = (today - self.next_payment_date).days
        
        # Check grace period (15 days in Nepal standard practice)
        if days_late <= 15:  # 15-day grace period
            return Decimal('0.00')
            
        # Apply fine calculation - 1% per month after due date (Nepal standard)
        monthly_rate = Decimal('0.01')  # 1% per month
        daily_rate = monthly_rate / Decimal('30')  # Approximate daily rate
        
        # Fine applies after grace period
        actual_days_late = days_late - 15
        
        # Ensure interval_payment is Decimal
        if isinstance(self.interval_payment, float):
            self.interval_payment = Decimal(str(self.interval_payment))
            
        fine = self.interval_payment * daily_rate * Decimal(str(actual_days_late))
        return max(fine.quantize(Decimal('1.00')), Decimal('0.00'))

    def is_current_period_paid(self):
        """Check if the current period has already been paid"""
        if not self.next_payment_date:
            # If there's no next payment date set, initialize it based on policy start date
            interval_months = {
                "quarterly": 3,
                "semi_annual": 6,
                "annual": 12,
                "Single": None  # Single payment policies are handled differently
            }.get(self.policy_holder.payment_interval)
            
            if not interval_months:
                return self.payment_status == 'Paid'  # For single payments
            
            # Calculate the initial next payment date based on policy start date
            today = date.today()
            policy_start = self.policy_holder.start_date
            
            # Calculate first payment date: start date + interval
            next_payment_date = policy_start.replace(
                month=((policy_start.month - 1 + interval_months) % 12) + 1,
                year=policy_start.year + ((policy_start.month - 1 + interval_months) // 12)
            )
            
            # Check if we need to calculate future periods based on difference
            if today > next_payment_date:
                # Calculate how many periods have passed
                months_diff = (today.year - next_payment_date.year) * 12 + today.month - next_payment_date.month
                periods_passed = months_diff // interval_months
                
                if periods_passed > 0:
                    # Adjust next payment date based on periods passed
                    next_payment_date = next_payment_date.replace(
                        month=((next_payment_date.month - 1 + (interval_months * periods_passed)) % 12) + 1,
                        year=next_payment_date.year + ((next_payment_date.month - 1 + (interval_months * periods_passed)) // 12)
                    )
            
            # Set the calculated next payment date
            self.next_payment_date = next_payment_date
            self.save(update_fields=['next_payment_date'])
            return False  # New or initialized payment date is never "already paid"
        
        # If next payment date is in the future, current period is paid
        today = date.today()
        interval_months = {
            "quarterly": 3,
            "semi_annual": 6,
            "annual": 12,
            "Single": None  # Single payment policies are handled differently
        }.get(self.policy_holder.payment_interval)
        
        if not interval_months:
            return self.payment_status == 'Paid'  # For single payments
            
        # Calculate the previous payment date
        last_payment_date = self.next_payment_date.replace(
            month=((self.next_payment_date.month - interval_months - 1) % 12) + 1,
            year=self.next_payment_date.year - ((self.next_payment_date.month - interval_months <= 0) and 1 or 0)
        )
        
        # If today is after last payment date but before next payment date, current period is paid
        return today > last_payment_date and today < self.next_payment_date

    def check_policy_expiry(self):
        """Check if policy should be expired due to long-term non-payment (3 years in Nepal)"""
        if self.payment_status == 'Paid' or self.policy_holder.status in ['Expired', 'Surrendered']:
            return False
        
        today = date.today()
        
        # If next payment date not set, calculate it based on policy start
        if not self.next_payment_date:
            interval_months = {
                "quarterly": 3,
                "semi_annual": 6,
                "annual": 12,
                "Single": None
            }.get(self.policy_holder.payment_interval)
            
            if not interval_months:
                return False  # Single payment policy can't expire due to missed regular payments
            
            policy_start = self.policy_holder.start_date
            self.next_payment_date = policy_start.replace(
                month=((policy_start.month - 1 + interval_months) % 12) + 1,
                year=policy_start.year + ((policy_start.month - 1 + interval_months) // 12)
            )
        
        # Calculate days late
        days_late = (today - self.next_payment_date).days
        
        # 3 years of non-payment leads to policy expiry (1095 days ≈ 3 years)
        if days_late > 1095:
            logger.info(f"Policy {self.policy_holder.id} has expired due to {days_late} days of non-payment")
            
            # Instead of just marking as expired, trigger automatic surrender
            surrender_reason = f"Automatic surrender due to non-payment for {days_late} days (over 3 years)"
            self.policy_holder.surrender_policy('Automatic', surrender_reason)
            
            # Update payment status
            self.payment_status = 'Expired'
            
            return True
        
        return False

    def __str__(self):
        return f"Premium Payment - {self.policy_holder.first_name} {self.policy_holder.last_name} ({self.payment_status})"

    class Meta:
        verbose_name = "Premium Payment"
        verbose_name_plural = "Premium Payments"

# Agent Report
class AgentReport(models.Model):
    agent = models.ForeignKey(SalesAgent, on_delete=models.CASCADE)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name='agent_reports', default=1)
    report_date = models.DateField()
    reporting_period = models.CharField(max_length=20)
    policies_sold = models.IntegerField(default=0)
    total_premium = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0, 
                                        help_text="Total commission earned from premium payments")
    target_achievement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    renewal_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    customer_retention = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    month = models.IntegerField(default=1)
    year = models.IntegerField(default=2000)

    def __str__(self):
        return f"Report for {self.agent} on {self.report_date}"
    
    class Meta:
        verbose_name = 'Agent Report'
        verbose_name_plural = 'Agent Reports'

class Loan(models.Model):
    policy_holder = models.ForeignKey('PolicyHolder', on_delete=models.CASCADE, related_name='loans')
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Principal loan amount.")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="Annual interest rate in percentage.")
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, editable=False, help_text="Remaining loan principal balance.")
    accrued_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, help_text="Interest accrued on the loan.")
    loan_status = models.CharField(
        max_length=50, 
        choices=[('Active', 'Active'), ('Paid', 'Paid')],
        default='Active'
    )
    last_interest_date = models.DateField(auto_now_add=True, help_text="Date when interest was last accrued.")
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now_add=True)

    def calculate_max_loan(self, requested_amount: Decimal = None) -> Dict[str, Union[bool, str, Decimal]]:
        """
        Calculate maximum loan amount and validate requested amount if provided.
        """
        # Check if policy is surrendered
        if self.policy_holder.status == 'Surrendered':
            return {
                'is_valid': False,
                'message': 'Cannot create loan for a surrendered policy',
                'max_allowed': Decimal('0'),
                'gsv_value': Decimal('0')
            }
        
        try:
            premium_payment = self.policy_holder.premium_payments.first()
            if not premium_payment:
                return {
                    'is_valid': False,
                    'message': 'No premium payments found for policy holder',
                    'max_allowed': Decimal('0'),
                    'gsv_value': Decimal('0')
                }
            
            gsv = premium_payment.gsv_value
            max_loan = gsv * Decimal('0.90')
            
            result = {
                'is_valid': True,
                'message': 'Maximum loan amount calculated',
                'max_allowed': max_loan,
                'gsv_value': gsv
            }
            
            if requested_amount is not None:
                if requested_amount <= Decimal('0'):
                    result.update({
                        'is_valid': False,
                        'message': 'Loan amount must be greater than 0',
                        'requested_amount': requested_amount
                    })
                elif requested_amount > max_loan:
                    result.update({
                        'is_valid': False,
                        'message': f'Loan amount exceeds maximum allowed amount of {max_loan}',
                        'requested_amount': requested_amount
                    })
                else:
                    result.update({
                        'message': 'Loan amount is valid',
                        'requested_amount': requested_amount
                    })
            
            return result
            
        except Exception as e:
            return {
                'is_valid': False,
                'message': f'Error calculating maximum loan: {str(e)}',
                'max_allowed': Decimal('0'),
                'gsv_value': Decimal('0')
            }

    def clean(self):
        """Validate the loan before saving."""
        if not self.pk:  # Only validate on creation
            validation = self.calculate_max_loan(self.loan_amount)
            if not validation['is_valid']:
                raise ValidationError({
                    'loan_amount': validation['message']
                })

    def save(self, *args, **kwargs):
        """Save the loan with validation."""
        try:
            self.full_clean()  # This will call our clean() method
            if not self.pk:  # On loan creation
                self.remaining_balance = self.loan_amount
            super().save(*args, **kwargs)
        except ValidationError as e:
            raise ValidationError(e.message_dict)
        except Exception as e:
            raise ValidationError({
                'non_field_errors': [f'Error saving loan: {str(e)}']
            })

    def accrue_interest(self):
        """Accrue interest on the remaining balance."""
        if self.loan_status != 'Active':
            return

        today = date.today()
        days_since_last_accrual = (today - self.last_interest_date).days

        if days_since_last_accrual <= 0:
            return

        try:
            daily_rate = self.interest_rate / 100 / 365
            interest = self.remaining_balance * Decimal(daily_rate) * Decimal(days_since_last_accrual)

            self.accrued_interest += interest.quantize(Decimal('1.00'))
            self.last_interest_date = today
            self.save()
        except Exception as e:
            raise ValidationError(f'Error accruing interest: {str(e)}')

    def __str__(self):
        return f"Loan for {self.policy_holder} - {self.loan_status}"
#Loan Repayment Model
class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    repayment_date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount paid towards the loan.")
    repayment_type = models.CharField(
        max_length=50, 
        choices=[('Principal', 'Principal'), ('Interest', 'Interest'), ('Both', 'Both')],
        default='Both'
    )
    remaining_loan_balance = models.DecimalField(max_digits=12, decimal_places=2, editable=False, help_text="Remaining loan balance after this repayment.")
    
    class Meta:
        ordering = ['-repayment_date']

    def process_repayment(self):
        """Apply repayment to interest and/or principal."""
        # Check if policy is surrendered
        if self.loan.policy_holder.status == 'Surrendered':
            raise ValidationError("Cannot process repayments for a surrendered policy.")
        
        # If this record already has a remaining_loan_balance, it's already been processed
        if self.pk and self.remaining_loan_balance > 0:
            return
        
        remaining = self.amount

        if self.repayment_type in ('Both', 'Interest'):
            # Deduct from accrued interest first
            interest_payment = min(remaining, self.loan.accrued_interest)
            self.loan.accrued_interest -= interest_payment
            remaining -= interest_payment

        if self.repayment_type in ('Both', 'Principal') and remaining > 0:
            # Deduct from remaining balance
            principal_payment = min(remaining, self.loan.remaining_balance)
            self.loan.remaining_balance -= principal_payment

        # Update loan status
        if self.loan.remaining_balance <= 0 and self.loan.accrued_interest <= 0:
            self.loan.loan_status = 'Paid'

        # Save the updated loan
        self.loan.save()

        # Set the remaining loan balance for this repayment
        self.remaining_loan_balance = self.loan.remaining_balance + self.loan.accrued_interest

    def save(self, *args, **kwargs):
        """Process repayment before saving."""
        # Always create new records, never update existing ones
        if not self.pk or not self.remaining_loan_balance:
            self.process_repayment()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Repayment for {self.loan} on {self.repayment_date}"

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        
    def __str__(self):
        return f"OTP for {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Set expiry to 10 minutes from now if not already set
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @classmethod
    def generate_otp(cls, user):
        # Generate a random 6-digit OTP
        otp_value = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Create new OTP object
        otp = cls.objects.create(
            user=user,
            otp=otp_value,
        )
        
        return otp

class Commission(models.Model):
    """Model to track agent commissions for premium payments."""
    agent = models.ForeignKey(
        'SalesAgent', 
        on_delete=models.CASCADE, 
        related_name='commissions'
    )
    policy_holder = models.ForeignKey(
        'PolicyHolder', 
        on_delete=models.CASCADE, 
        related_name='commissions'
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        help_text="Commission amount"
    )
    date = models.DateField(
        help_text="Date commission was recorded"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Paid', 'Paid'),
            ('Rejected', 'Rejected')
        ],
        default='Pending'
    )
    payment_date = models.DateField(
        null=True, 
        blank=True, 
        help_text="Date commission was paid"
    )
    notes = models.TextField(
        blank=True, 
        null=True, 
        help_text="Additional notes about this commission"
    )
    
    def __str__(self):
        return f"Commission {self.amount} for {self.agent.first_name} - {self.policy_holder.policy_number}"
    
    class Meta:
        verbose_name = "Commission"
        verbose_name_plural = "Commissions"
        ordering = ['-date']

# Policy Surrender Process
class PolicySurrender(models.Model):
    """Model to handle policy surrender requests and processing."""
    policy_holder = models.ForeignKey(
        PolicyHolder,
        on_delete=models.CASCADE,
        related_name='surrender_requests'
    )
    request_date = models.DateField(
        auto_now_add=True,
        help_text="Date when surrender was requested"
    )
    surrender_type = models.CharField(
        max_length=20,
        choices=[
            ('Voluntary', 'Voluntary Surrender'),
            ('Automatic', 'Automatic Surrender'),
            ('Maturity', 'Maturity Surrender')
        ],
        default='Voluntary',
        help_text="Type of surrender request"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Approved', 'Approved'),
            ('Rejected', 'Rejected'),
            ('Processed', 'Processed')
        ],
        default='Pending'
    )
    gsv_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Guaranteed Surrender Value at time of request"
    )
    ssv_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Special Surrender Value at time of request"
    )
    surrender_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Final surrender amount to be paid"
    )
    outstanding_loans = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Outstanding loan amount to be deducted"
    )
    processing_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Fee charged for processing surrender"
    )
    tax_deduction = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Tax deducted on surrender amount (TDS)"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_surrenders'
    )
    approval_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when surrender was approved"
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when surrender amount was paid"
    )
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('Bank Transfer', 'Bank Transfer'),
            ('Check', 'Check'),
            ('Cash', 'Cash')
        ],
        null=True,
        blank=True
    )
    surrender_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for surrender request"
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Additional notes about surrender process"
    )
    
    def calculate_surrender_values(self):
        """Calculate surrender values (GSV and SSV)."""
        try:
            premium_payment = self.policy_holder.premium_payments.first()
            if not premium_payment:
                return
                
            # Get GSV and SSV values from premium payment
            self.gsv_amount = premium_payment.gsv_value
            self.ssv_amount = premium_payment.ssv_value
            
            # Get outstanding loans
            outstanding_loans = self.policy_holder.loans.filter(
                loan_status='Active'
            ).aggregate(
                total=Sum('remaining_balance') + Sum('accrued_interest')
            )['total'] or Decimal('0.00')
            
            self.outstanding_loans = outstanding_loans
            
            # Calculate processing fee (typically 1-2% in Nepal)
            processing_fee_rate = Decimal('0.01')  # 1%
            max_surrender = max(self.gsv_amount, self.ssv_amount)
            self.processing_fee = (max_surrender * processing_fee_rate).quantize(Decimal('1.00'))
            
            # Calculate TDS (tax) - typically 15% on the surrender profit in Nepal
            # If policy surrendered after 5 years, tax is usually exempted
            policy_duration = (date.today() - self.policy_holder.start_date).days // 365
            
            if policy_duration < 5 and max_surrender > 0:
                # Calculate taxable amount (surrender value minus total premiums paid)
                premium_payment = self.policy_holder.premium_payments.first()
                total_premiums = premium_payment.total_paid if premium_payment else Decimal('0.00')
                taxable_amount = max(max_surrender - total_premiums, Decimal('0.00'))
                
                # Apply TDS rate (15% in Nepal)
                tds_rate = Decimal('0.15')
                self.tax_deduction = (taxable_amount * tds_rate).quantize(Decimal('1.00'))
            else:
                self.tax_deduction = Decimal('0.00')
            
            # Calculate final surrender amount
            self.surrender_amount = max(
                max_surrender - self.outstanding_loans - self.processing_fee - self.tax_deduction,
                Decimal('0.00')
            )
            
            return {
                'gsv': self.gsv_amount,
                'ssv': self.ssv_amount,
                'surrender_amount': self.surrender_amount,
                'outstanding_loans': self.outstanding_loans,
                'processing_fee': self.processing_fee,
                'tax_deduction': self.tax_deduction
            }
            
        except Exception as e:
            logger.error(f"Error calculating surrender values: {str(e)}")
            raise ValidationError(f"Error calculating surrender values: {str(e)}")
    
    def approve_surrender(self, user):
        """Approve surrender request and calculate final values."""
        if self.status == 'Approved':
            raise ValidationError("This surrender is already approved.")
        
        if self.status != 'Pending' and self.status != 'Processed':
            raise ValidationError("Cannot approve a surrender that is not in pending or processed status")
        
        self.calculate_surrender_values()
        self.approved_by = user
        self.approval_date = date.today()
        self.status = 'Approved'
        self.save()
        
        # Update policy holder status
        self.policy_holder.status = 'Surrendered'
        self.policy_holder.save(update_fields=['status'])
        
        return True
    
    def process_payment(self, payment_method):
        """Process surrender payment."""
        if self.status != 'Approved':
            raise ValidationError("Cannot process payment for a surrender that is not approved")
        
        self.payment_method = payment_method
        self.payment_date = date.today()
        self.status = 'Processed'
        self.save()
        
        # Ensure policy holder status is set to Surrendered
        if self.policy_holder.status != 'Surrendered':
            self.policy_holder.status = 'Surrendered'
            self.policy_holder.save(update_fields=['status'])
        
        return True
    
    def save(self, *args, **kwargs):
        # For new surrender requests, calculate surrender values
        if not self.pk:
            self.calculate_surrender_values()
        
        # For automatic surrenders, auto-approve only if status is Pending
        if not self.pk and self.surrender_type == 'Automatic' and self.status == 'Pending':
            self.status = 'Approved'
            self.approval_date = date.today()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Surrender: {self.policy_holder} - {self.status} ({self.surrender_amount})"
    
    class Meta:
        verbose_name = "Policy Surrender"
        verbose_name_plural = "Policy Surrenders"
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['policy_holder']),
            models.Index(fields=['status']),
        ]

class PolicyRenewal(models.Model):
    """Model to track policy renewals and send notifications."""
    RENEWAL_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Renewed', 'Renewed'),
        ('Expired', 'Expired'),
    ]
    
    policy_holder = models.ForeignKey(
        'PolicyHolder', 
        on_delete=models.CASCADE, 
        related_name='renewals'
    )
    due_date = models.DateField(
        help_text="Date when policy renewal is due"
    )
    renewal_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Amount needed for renewal"
    )
    status = models.CharField(
        max_length=20,
        choices=RENEWAL_STATUS_CHOICES,
        default='Pending'
    )
    grace_period_end = models.DateField(
        null=True, 
        blank=True,
        help_text="End date of grace period for renewal"
    )
    renewal_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when the policy was renewed"
    )
    renewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User who processed the renewal"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes about this renewal"
    )
    
    # Reminder tracking fields
    first_reminder_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when first reminder was sent"
    )
    is_first_reminder_sent = models.BooleanField(
        default=False,
        help_text="Indicates if first reminder has been sent"
    )
    
    second_reminder_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when second reminder was sent"
    )
    is_second_reminder_sent = models.BooleanField(
        default=False,
        help_text="Indicates if second reminder has been sent"
    )
    
    final_reminder_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date when final reminder was sent"
    )
    is_final_reminder_sent = models.BooleanField(
        default=False,
        help_text="Indicates if final reminder has been sent"
    )
    
    def __str__(self):
        return f"Renewal for {self.policy_holder.policy_number} due on {self.due_date}"
    
    def save(self, *args, **kwargs):
        # Calculate grace period end date (30 days after due date)
        if not self.grace_period_end and self.due_date:
            self.grace_period_end = self.due_date + timedelta(days=30)
            
        # Auto-expire if past grace period
        if self.status == 'Pending' and self.grace_period_end and date.today() > self.grace_period_end:
            self.status = 'Expired'
            
            # Update policy holder status if needed
            if self.policy_holder.status == 'Active':
                self.policy_holder.status = 'Expired'
                self.policy_holder.save(update_fields=['status'])
        
        super().save(*args, **kwargs)
    
    def mark_as_renewed(self, user):
        """Mark the policy as renewed."""
        if self.status in ['Pending', 'Expired']:
            self.status = 'Renewed'
            self.renewal_date = date.today()
            self.renewed_by = user
            self.save()
            
            # Update policy holder record
            self.policy_holder.start_date = date.today()
            self.policy_holder.maturity_date = date.today().replace(
                year=date.today().year + self.policy_holder.duration_years
            )
            self.policy_holder.status = 'Active'
            self.policy_holder.save(update_fields=[
                'start_date', 'maturity_date', 'status'
            ])
            
            # Create a new premium payment record if needed
            try:
                premium_payment = self.policy_holder.premium_payments.first()
                if premium_payment:
                    premium_payment.calculate_premium()
                    premium_payment.payment_status = 'Unpaid'
                    premium_payment.save()
            except Exception as e:
                logger.error(f"Error updating premium payment for renewal: {str(e)}")
            
            return True
        return False
    
    def check_expiry(self):
        """Check if the renewal period has expired."""
        today = date.today()
        
        if self.status == 'Pending' and self.grace_period_end and today > self.grace_period_end:
            self.status = 'Expired'
            self.save(update_fields=['status'])
            
            # Update policy holder status if needed
            if self.policy_holder.status == 'Active':
                self.policy_holder.status = 'Expired'
                self.policy_holder.save(update_fields=['status'])
                
            return True
        return False
    
    def __str__(self):
        return f"Renewal for {self.policy_holder.policy_number} - Due: {self.due_date}"
    
    class Meta:
        verbose_name = "Policy Renewal"
        verbose_name_plural = "Policy Renewals"
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['policy_holder']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]

def save(self, *args, **kwargs):
    if not self.pk:  # New instance
        self.annual_premium, self.interval_payment = self.calculate_premium()

        if self.policy_holder.payment_interval == "Single":
            self.total_premium = self.interval_payment
        else:
            self.total_premium = self.annual_premium * Decimal(str(self.policy_holder.duration_years))

    # Convert all monetary values to Decimal to prevent type errors
    if isinstance(self.total_premium, float):
        self.total_premium = Decimal(str(self.total_premium))
    if isinstance(self.total_paid, float):
        self.total_paid = Decimal(str(self.total_paid))
    if isinstance(self.paid_amount, float):
        self.paid_amount = Decimal(str(self.paid_amount))
    if isinstance(self.fine_due, float):
        self.fine_due = Decimal(str(self.fine_due))
    if isinstance(self.fine_paid, float):
        self.fine_paid = Decimal(str(self.fine_paid))

    # Handle new payment if paid_amount is provided
    if self.paid_amount > 0:
        # Calculate taxes
        self.calculate_taxes()
        
        # Generate receipt number if not provided
        if not self.receipt_number:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.receipt_number = f"RCP-{self.policy_holder.policy_number}-{timestamp}"
            
        # First add to total_paid
        self.total_paid += self.paid_amount
        self.paid_amount = Decimal('0.00')  # Reset paid_amount after adding to total_paid
    
    # Update remaining premium (doesn't include fines)
    self.remaining_premium = max(self.total_premium - self.total_paid, Decimal('0.00'))

    # Update payment status based on premium (not including fines)
    if self.total_paid >= self.total_premium:
        self.payment_status = 'Paid'
    elif self.total_paid > 0:
        self.payment_status = 'Partially Paid'
    else:
        self.payment_status = 'Unpaid'

    # Calculate and apply fine if not already set and no existing fine
    if self.fine_due <= 0:
        self.fine_due = self.calculate_fine()

    # Check for policy expiry due to non-payment
    self.check_policy_expiry()

    # --- New GSV and SSV Calculations ---
    self.gsv_value = self.calculate_gsv()
    self.ssv_value = self.calculate_ssv()
        
    super().save(*args, **kwargs)