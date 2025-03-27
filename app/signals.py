from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db import transaction, DatabaseError, IntegrityError
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
import logging
from functools import wraps
from django.db.models import F, Sum

from .models import (
    PolicyHolder, 
    Underwriting, 
    PremiumPayment, 
    InsurancePolicy, 
    AgentReport, 
    AgentApplication, 
    SalesAgent,
    Loan,
    LoanRepayment,
    ClaimProcessing,
    ClaimRequest,
    PaymentProcessing,
    Branch,
    Company,
    UserProfile,
    Bonus,
    Commission
)
import random

# Configure logger
logger = logging.getLogger(__name__)

def transaction_retry(max_attempts=3, delay=1):
    """Decorator to retry database operations on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_attempts:
                try:
                    with transaction.atomic():
                        return func(*args, **kwargs)
                except (DatabaseError, IntegrityError) as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Transaction failed after {max_attempts} attempts: {str(e)}")
                        raise
                    logger.warning(f"Transaction attempt {attempt} failed: {str(e)}. Retrying...")
                    import time
                    time.sleep(delay * (2 ** (attempt - 1)))  # Exponential backoff
        return wrapper
    return decorator

# Signal dispatch order control with dispatch_uid
@receiver(post_save, sender=PolicyHolder, dispatch_uid="policy_holder_post_save_handler")
def policy_holder_post_save(sender, instance, created, **kwargs):
    """
    Master signal handler for all PolicyHolder post-save operations.
    This ensures operations happen in the correct order within a transaction.
    """
    # Skip if this is a signal-triggered save to prevent recursion
    if getattr(instance, '_skip_signal', False):
        return
        
    try:
        with transaction.atomic():
            # Create/update underwriting before premium management
            if instance.status in ['Pending', 'Active']:
                underwriting, created = Underwriting.objects.get_or_create(policy_holder=instance)
                # Update underwriting without triggering recursion
                if not getattr(underwriting, '_from_signal', False):
                    underwriting._from_signal = True
                    underwriting.save()
                    underwriting._from_signal = False
            
            # Create/update premium payment for approved/active policies
            if instance.status in ['Approved', 'Active']:
                premium, created = PremiumPayment.objects.get_or_create(
                    policy_holder=instance,
                    defaults={
                        'payment_interval': instance.payment_interval,
                        'payment_mode': instance.payment_mode
                    }
                )
                if not created:
                    premium.save()  # Ensure calculations are updated
                
            # Handle policy maturity date calculation
            if created or not instance.maturity_date:
                if instance.start_date and instance.duration_years:
                    instance._skip_signal = True  # Prevent recursion
                    instance.calculate_maturity_date()
                    instance.save(update_fields=['maturity_date'])
                    instance._skip_signal = False
                    
            # Update agent statistics
            if created and instance.agent:
                update_agent_stats(instance)
                
            # Check for policy anniversary (if not a new policy)
            if not created and instance.status == 'Active':
                check_policy_anniversary(instance)
                
    except Exception as e:
        logger.error(f"Error in policy_holder_post_save for policy ID {instance.id}: {str(e)}")
        # Don't re-raise to avoid disrupting the user experience
        # But consider alerting an admin in production

def update_agent_stats(policy_holder):
    """Extract agent statistics update logic to a separate function for clarity"""
    try:
        with transaction.atomic():
            agent = policy_holder.agent
            
            # Update agent's total policies
            agent.total_policies_sold += 1
            agent.last_policy_date = timezone.now().date()
            agent.save()

            # Create or update the monthly report
            report_date = timezone.now().date()
            report, created = AgentReport.objects.get_or_create(
                agent=agent,
                branch=agent.branch,
                report_date=report_date.replace(day=1),  # First day of current month
                defaults={
                    'reporting_period': f"{report_date.year}-{report_date.month}",
                    'policies_sold': 0,
                    'total_premium': Decimal('0.00'),
                    'commission_earned': Decimal('0.00'),
                    'target_achievement': Decimal('0.00'),
                    'renewal_rate': Decimal('0.00'),
                    'customer_retention': Decimal('0.00'),
                }
            )
            
            report.policies_sold += 1
            report.save()
    except Exception as e:
        logger.error(f"Error updating agent stats: {str(e)}")

def check_policy_anniversary(policy_holder):
    """Check if today is the policy's anniversary for bonus calculation"""
    today = date.today()
    
    if (policy_holder.start_date.month == today.month and 
        policy_holder.start_date.day == today.day and
        policy_holder.status == 'Active'):
        
        # Check for existing bonus for the year
        if not Bonus.objects.filter(
            policy_holder=policy_holder, 
            start_date__year=today.year
        ).exists():
            try:
                Bonus.objects.create(
                    policy_holder=policy_holder,
                    start_date=today
                )
                logger.info(f"Created anniversary bonus for policy {policy_holder.id}")
            except Exception as e:
                logger.error(f"Bonus creation failed for policy {policy_holder.id}: {str(e)}")

@receiver(post_save, sender=Underwriting)
def update_policy_holder_from_underwriting(sender, instance, **kwargs):
    """Update PolicyHolder's risk category based on Underwriting."""
    # Skip updates if manual_override is enabled or to prevent recursion
    if instance.manual_override or getattr(instance, '_from_signal', False):
        return

    try:
        policy_holder = instance.policy_holder

        # Only update if the risk category has changed
        if policy_holder.risk_category != instance.risk_category:
            policy_holder._skip_signal = True  # Prevent recursion
            policy_holder.risk_category = instance.risk_category
            policy_holder.save(update_fields=['risk_category'])
            policy_holder._skip_signal = False
            logger.info(f"Updated risk category for policy {policy_holder.id} to {instance.risk_category}")
    except Exception as e:
        logger.error(f"Error updating policy holder from underwriting: {str(e)}")
        
@receiver(pre_delete, sender=PolicyHolder)
def cleanup_policy_holder(sender, instance, **kwargs):
    """
    Clean up related records when PolicyHolder is deleted:
    - Deletes premium payments
    - Deletes underwriting records
    - Removes uploaded documents
    """
    try:
        # Delete related records
        PremiumPayment.objects.filter(policy_holder=instance).delete()
        Underwriting.objects.filter(policy_holder=instance).delete()
        
        # Delete uploaded files
        file_fields = [
            'document_front', 
            'document_back', 
            'pp_photo', 
            'pan_front', 
            'pan_back', 
            'nominee_document_front',
            'nominee_document_back', 
            'nominee_pp_photo',
            'past_medical_report',
            'recent_medical_reports'
        ]
        
        for field in file_fields:
            document = getattr(instance, field, None)
            if document:
                try:
                    document.delete(save=False)
                except Exception as e:
                    logger.error(f"Error deleting {field}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in cleanup_policy_holder signal: {str(e)}")

@receiver(post_save, sender='app.PremiumPayment')
def premium_payment_post_save(sender, instance, created, **kwargs):
    """Signal handler for post-save operations on PremiumPayment."""
    try:
        logger.info(f"Premium payment post-save signal triggered for {instance}")
        
        # Update policy holder payment status based on premium payments
        update_policy_holder_payment_status(instance.policy_holder)
        
        # Update agent reports and commission if applicable
        update_agent_report_and_commission(instance)
        
    except Exception as e:
        logger.error(f"Error in premium_payment_post_save: {e}")

def update_policy_holder_payment_status(policy_holder):
    """Update the payment status of a PolicyHolder based on premium payments."""
    try:
        # Get the premium payment for this policy
        premium_payment = policy_holder.premium_payments.first()
        
        if not premium_payment:
            return
            
        # Log current values
        logger.info(f"Updating payment status for {policy_holder.id}: " 
                   f"total_paid={premium_payment.total_paid}, "
                   f"total_premium={premium_payment.total_premium}")
            
        # Determine payment status
        if premium_payment.total_paid >= premium_payment.total_premium:
            policy_holder.payment_status = 'Paid'
        elif premium_payment.total_paid > 0:
            policy_holder.payment_status = 'Partially Paid'
        else:
            policy_holder.payment_status = 'Unpaid'
            
        policy_holder.save(update_fields=['payment_status'])
        logger.info(f"Updated {policy_holder.id} status to {policy_holder.payment_status}")
            
    except Exception as e:
        logger.error(f"Error in update_policy_holder_payment_status: {e}")

def update_agent_report_and_commission(premium_payment):
    """Update agent report and commission when a premium payment is made."""
    try:
        policy_holder = premium_payment.policy_holder
        
        # Skip if no agent is assigned
        if not hasattr(policy_holder, 'agent') or not policy_holder.agent:
            return
            
        # Get or create agent report
        report, created = AgentReport.objects.get_or_create(
            agent=policy_holder.agent,
            month=date.today().month,
            year=date.today().year
        )
        
        # Calculate commission amount
        commission_rate = getattr(policy_holder.agent, 'commission_rate', None)
        if not commission_rate:
            commission_rate = Decimal('0.15')  # Default 15%
            
        # Only calculate commission on the newly paid amount
        commission_amount = premium_payment.paid_amount * commission_rate
        
        # Create commission record
        if commission_amount > 0:
            Commission.objects.create(
                agent=policy_holder.agent,
                policy_holder=policy_holder,
                amount=commission_amount,
                date=date.today(),
                status='Pending'
            )
            
            # Update agent report
            report.total_premium = F('total_premium') + premium_payment.paid_amount
            report.total_commission = F('total_commission') + commission_amount
            report.save()
            
            logger.info(f"Created commission of {commission_amount} for agent {policy_holder.agent.id}")
            
    except Exception as e:
        logger.error(f"Error in update_agent_report_and_commission: {e}")
        
        
@receiver(post_save, sender='app.PolicyHolder')
def policy_holder_post_save(sender, instance, created, **kwargs):
    """Signal handler for post-save operations on PolicyHolder"""
    try:
        # Don't proceed if this is a modification and payment_status hasn't changed
        if not created and 'payment_status' not in kwargs.get('update_fields', []):
            return

        # Check if premium payment exists
        premium_payment = instance.premium_payments.first()
        
        # Create new premium payment if doesn't exist and policy is approved
        if not premium_payment and instance.status == 'Approved':
            logger.info(f"Creating premium payment for {instance.id}")
            premium_payment = PremiumPayment.objects.create(
                policy_holder=instance
            )
            
            # Force premium calculation
            annual, interval = premium_payment.calculate_premium()
            premium_payment.annual_premium = annual
            premium_payment.interval_payment = interval
            
            # Set total premium based on duration and payment interval
            if instance.payment_interval == "Single":
                premium_payment.total_premium = interval
            else:
                premium_payment.total_premium = annual * Decimal(str(instance.duration_years))
                
            premium_payment.save()
            
            logger.info(f"Created premium payment: annual={annual}, interval={interval}, total={premium_payment.total_premium}")
            
            # Create initial underwriting if it doesn't exist
            if not hasattr(instance, 'underwriting'):
                from .models import Underwriting
                Underwriting.objects.create(
                    policy_holder=instance,
                    status='Pending',
                    assessment_date=date.today()
                )
    except Exception as e:
        logger.error(f"Error in policy_holder_post_save: {e}")

@receiver(post_save, sender=AgentApplication)
def agent_application_approval(sender, instance, created, **kwargs):
    """Create SalesAgent when application is approved."""
    try:
        if instance.status.upper() == "APPROVED" and not SalesAgent.objects.filter(application=instance).exists():
            agent_code = f"A-{instance.branch.id}-{str(instance.id).zfill(4)}"
            
            # Create User for authentication
            username = instance.phone_number  # Use phone number as username
            
            # Check if a user with this username already exists
            if not User.objects.filter(username=username).exists():
                # Create new user
                user = User.objects.create_user(
                    username=username,
                    email=instance.email,
                    password="agent123",  # Default password
                    first_name=instance.first_name,
                    last_name=instance.last_name
                )
            else:
                # Get existing user if already exists
                user = User.objects.get(username=username)
            
            # Create SalesAgent and link to User
            sales_agent = SalesAgent.objects.create(
                user=user,
                branch=instance.branch,
                application=instance,
                agent_code=agent_code,
                commission_rate=Decimal('5.00'),  # Default commission rate
                is_active=True,
                joining_date=date.today(),
                status='ACTIVE',
                phone_number=instance.phone_number,
                email=instance.email
            )
            
            logger.info(f"Created new sales agent from application {instance.id}")
    except Exception as e:
        logger.error(f"Error in agent_application_approval: {str(e)}")

# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update UserProfile when User is created/updated."""
    try:
        if created:
            profile = UserProfile.objects.create(user=instance)
            if not instance.is_superuser:
                first_company = Company.objects.first()
                if first_company:
                    profile.company = first_company
                    profile.save()
                    logger.info(f"Created user profile for {instance.username}")
    except Exception as e:
        logger.error(f"Error creating user profile: {str(e)}")

@receiver(post_save, sender=Loan)
def accrue_interest_on_loan_save(sender, instance, **kwargs):
    """Automatically accrue interest when a loan is saved."""
    try:
        # Skip if this is from a signal to prevent recursion
        if getattr(instance, '_from_signal', False):
            return
            
        instance._from_signal = True
        instance.accrue_interest()
        instance._from_signal = False
    except Exception as e:
        logger.error(f"Error accruing interest on loan {instance.id}: {str(e)}")

@receiver(post_save, sender=LoanRepayment)
def process_loan_repayment(sender, instance, created, **kwargs):
    """Process loan repayment and update loan status."""
    if not created:
        return  # Only process new repayments
        
    try:
        with transaction.atomic():
            loan = instance.loan
            
            # Skip if this is from a signal to prevent recursion
            if getattr(loan, '_from_signal', False):
                return
            
            # Skip process_repayment() since it's already called in the save method
            # Simply update the loan status if needed
            
            # Check if loan is fully paid
            if loan.remaining_balance <= 0 and loan.accrued_interest <= 0:
                loan._from_signal = True
                loan.loan_status = 'Paid'
                loan.save(update_fields=['loan_status'])
                loan._from_signal = False
                logger.info(f"Loan {loan.id} marked as fully paid")
    except Exception as e:
        logger.error(f"Error processing loan repayment {instance.id}: {str(e)}")

#Trigger Claim Processing wheneve the claim request is created
@receiver(post_save, sender=ClaimRequest)
def create_claim_processing(sender, instance, created, **kwargs):
    """Create claim processing when a claim request is created."""
    if not created:
        return
        
    try:
        ClaimProcessing.objects.create(
            branch=instance.branch,
            claim_request=instance
        )
        logger.info(f"Created claim processing for claim request {instance.id}")
    except Exception as e:
        logger.error(f"Error creating claim processing: {str(e)}")

# automatically mark the paid once the payment is approved
@receiver(post_save, sender=ClaimProcessing)
def auto_finalize_payment(sender, instance, **kwargs):
    try:
        if instance.processing_status == 'Approved':
            PaymentProcessing.objects.filter(claim_request=instance.claim_request).update(
                processing_status='Completed'
            )
            logger.info(f"Auto-finalized payment for claim {instance.claim_request.id}")
    except Exception as e:
        logger.error(f"Error finalizing payment: {str(e)}")

@receiver(post_save, sender=PolicyHolder)
def create_policyholder_user(sender, instance, created, **kwargs):
    """Create User account for PolicyHolder if it doesn't exist."""
    if created and instance.phone_number and not instance.user:
        try:
            # Use phone number as username
            username = instance.phone_number
            
            # Check if user already exists
            if not User.objects.filter(username=username).exists():
                # Create a random password (they can reset it later via OTP)
                # or set a default password they must change
                password = ''.join([str(random.randint(0, 9)) for _ in range(8)])
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=instance.email,
                    password=password,
                    first_name=instance.first_name,
                    last_name=instance.last_name
                )
                
                # Link user to policy holder
                instance.user = user
                instance.save(update_fields=['user'])
                
                logger.info(f"Created user account for policy holder {instance.id}")
            else:
                # If user exists, link it
                user = User.objects.get(username=username)
                instance.user = user
                instance.save(update_fields=['user'])
                
        except Exception as e:
            logger.error(f"Error creating user for policy holder {instance.id}: {str(e)}")
