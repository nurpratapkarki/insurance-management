from django.db.models.signals import post_save, pre_delete,pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from datetime import date
from django.utils import timezone
from django.contrib.auth.models import User
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
    Bonus
)

@receiver(post_save, sender=PolicyHolder)
def policy_holder_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for PolicyHolder."""
    try:
        with transaction.atomic():
            # Create PremiumPayment for approved/active policies
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
            
    except Exception as e:
        print(f"Error in policy_holder_post_save signal: {str(e)}")




@receiver(post_save, sender=PolicyHolder)
def create_or_update_underwriting(sender, instance, created, **kwargs):
    """Create or update underwriting for active or pending policyholders."""
    # Avoid infinite recursion by skipping updates caused by the signal itself
    if getattr(instance, '_from_signal', False):
        return
    
    if instance.status in ['Pending', 'Active']:
        underwriting, _ = Underwriting.objects.get_or_create(policy_holder=instance)

        # Save underwriting without triggering PolicyHolder updates
        underwriting._from_signal = True
        underwriting.save()
        underwriting._from_signal = False
@receiver(post_save, sender=Underwriting)
def update_policy_holder_from_underwriting(sender, instance, **kwargs):
    """Update PolicyHolder's risk category based on Underwriting."""
    # Skip updates if manual_override is enabled
    if instance.manual_override:
        return

    policy_holder = instance.policy_holder

    # Only update if the risk category has changed
    if policy_holder.risk_category != instance.risk_category:
        policy_holder.risk_category = instance.risk_category
        policy_holder.save()
        
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
                    print(f"Error deleting {field}: {str(e)}")
                
    except Exception as e:
        print(f"Error in cleanup_policy_holder signal: {str(e)}")

@receiver(post_save, sender=PremiumPayment)
def update_policy_holder_payment_status(sender, instance, **kwargs):
    """
    Update PolicyHolder payment status when premium payment changes
    """
    try:
        policy_holder = instance.policy_holder
        
        # Calculate new status based on payment amounts
        if instance.total_paid >= instance.total_premium_due:
            new_status = 'Paid'
        elif instance.total_paid > 0:
            new_status = 'Partially Paid'
        else:
            new_status = 'Due'
            
        # Update only if status has changed
        if policy_holder.payment_status != new_status:
            PolicyHolder.objects.filter(id=policy_holder.id).update(
                payment_status=new_status
            )
            
    except Exception as e:
        print(f"Error updating payment status: {str(e)}")

# Signal for new PolicyHolder creation
@receiver(post_save, sender=PolicyHolder)
def update_agent_stats_on_new_policy(sender, instance, created, **kwargs):
    """Update agent statistics when a new policy is created"""
    if created and instance.agent:
        with transaction.atomic():
            agent = instance.agent
            
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

@receiver(post_save, sender=PremiumPayment)
def update_agent_report_and_commission(sender, instance, created, **kwargs):
    """Update agent report and commission when a premium payment is made"""
    if not instance.policy_holder.agent:
        return

    try:
        with transaction.atomic():
            agent = instance.policy_holder.agent
            report_date = instance.next_payment_date or timezone.now().date()
            
            # Get or create monthly report
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

            if created:
                # New premium payment
                commission = (instance.interval_payment * agent.commission_rate / 100)
                
                # Update report
                report.total_premium += instance.interval_payment
                report.commission_earned += commission
                
                # Update agent's total premium collected
                agent.total_premium_collected += instance.interval_payment
                agent.save()
                
            # Calculate target achievement (assuming monthly target is stored somewhere)
            # This is a placeholder - adjust according to your target logic
            if hasattr(agent, 'monthly_target'):
                report.target_achievement = (report.total_premium / agent.monthly_target) * 100
                
            # Calculate renewal rate (if applicable)
            # This is a placeholder - adjust according to your renewal logic
            total_policies = PolicyHolder.objects.filter(agent=agent).count()
            renewed_policies = PolicyHolder.objects.filter(
                agent=agent,
                status='ACTIVE',
                maturity_date__gte=report_date  
            ).count()


            
            if total_policies > 0:
                report.renewal_rate = (renewed_policies / total_policies) * 100
            report.save()
            
    except Exception as e:
        print(f"Error in update_agent_report_and_commission signal: {str(e)}")
        raise

# # Optional: Add a pre_save signal to validate premium payments
# @receiver(pre_save, sender=PremiumPayment)
# def validate_premium_payment(sender, instance, **kwargs):
#     """Validate premium payment before saving"""
#     if instance.interval_payment <= 0:
#         raise ValueError("Premium payment amount must be greater than zero")
    
#     if not instance.policy_holder:
#         raise ValueError("Premium payment must be associated with a policy holder")

    #  Add signal to handle agent application approval
@receiver(post_save, sender=AgentApplication)
def agent_application_approval(sender, instance, created, **kwargs):
    """Create SalesAgent when application is approved."""
    try:
        if instance.status.upper() == "APPROVED" and not SalesAgent.objects.filter(application=instance).exists():
            agent_code = f"A-{instance.branch.id}-{str(instance.id).zfill(4)}"
            SalesAgent.objects.create(
                branch=instance.branch,
                application=instance,
                agent_code=agent_code,
                commission_rate=Decimal('5.00'),  # Default commission rate
                is_active=True,
                joining_date=date.today(),
                status='ACTIVE'
            )
    except Exception as e:
        print(f"Error in agent_application_approval signal: {str(e)}")
        raise

            
    except Exception as e:
        print(f"Error in agent_application_approval signal: {str(e)}")
        raise  # Re-raise the exception to ensure it's not silently ignored

# Optional: Add signal to handle policy renewal
@receiver(post_save, sender=PolicyHolder)
def handle_policy_renewal(sender, instance, **kwargs):
    """
    Handle policy renewal processes
    - Triggered when policy status changes
    - Creates renewal notices
    - Updates related records
    """
    try:
        # Check if policy is near maturity (e.g., within 30 days)
        if instance.maturity_date and instance.status == 'Active':
            today = date.today()
            days_to_maturity = (instance.maturity_date - today).days
            
            if 0 < days_to_maturity <= 30:
                # You can add renewal notification logic here
                pass
                
    except Exception as e:
        print(f"Error in handle_policy_renewal signal: {str(e)}")
    from django.db.models import Q

@receiver(post_save, sender=PolicyHolder)
def trigger_bonus_on_anniversary(sender, instance, **kwargs):
    """Trigger bonus calculation on policyholder's anniversary."""
    today = date.today()
    
    # Ensure policy is active and it is the anniversary
    if instance.status == 'Active' and instance.start_date.month == today.month and instance.start_date.day == today.day:
        # Check for existing bonus for the year
        if not Bonus.objects.filter(
            policy_holder=instance, 
            start_date__year=today.year
        ).exists():
            try:
                Bonus.objects.create(
                    policy_holder=instance,
                    start_date=today
                )
            except ValueError as e:
                print(f"Bonus creation failed: {e}")



@receiver(post_save, sender=Loan)
def accrue_interest_on_loan_save(sender, instance, **kwargs):
    """Automatically accrue interest when a loan is saved."""
    instance.accrue_interest()

@receiver(post_save, sender=LoanRepayment)
def reset_interest_on_repayment(sender, instance, **kwargs):
    """Reset interest accrual after a repayment is processed."""
    instance.loan.accrue_interest()

#Trigger Claim Processing wheneve the claim request is created
@receiver(post_save, sender=ClaimRequest)
def create_claim_processing(sender, instance, created, **kwargs):
    """Create claim processing when a claim request is created."""
    if created:
        ClaimProcessing.objects.create(
            branch=instance.branch,
            claim_request=instance
        )
# automatically mark the paid onece the payment  is approved
@receiver(post_save, sender=ClaimProcessing)
def auto_finalize_payment(sender, instance, **kwargs):
    if instance.processing_status == 'Approved':
        PaymentProcessing.objects.filter(claim_request=instance.claim_request).update(
            processing_status='Completed'
        )

# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update UserProfile when User is created/updated."""
    if created:
        profile = UserProfile.objects.create(user=instance)
        if not instance.is_superuser:
            first_company = Company.objects.first()
            if first_company:
                profile.company = first_company
                profile.save()
