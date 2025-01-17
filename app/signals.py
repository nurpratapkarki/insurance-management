from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from datetime import date
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
    PaymentProcessing
)

@receiver(post_save, sender=PolicyHolder)
def policy_holder_post_save(sender, instance, created, **kwargs):
    """
    Handle all post-save operations for PolicyHolder:
    - Creates/updates premium payments for approved/active policies
    - Creates underwriting records for pending policies
    - Updates related records
    """
    try:
        with transaction.atomic():
            # Create or update PremiumPayment for approved/active policies
            if instance.status in ['Approved', 'Active']:
                premium_payment, created = PremiumPayment.objects.get_or_create(
                    policy_holder=instance,
                    defaults={
                        'payment_interval': instance.payment_interval,
                        'payment_mode': instance.payment_mode
                    }
                )
                
                if created or instance.sum_assured != getattr(premium_payment, '_original_sum_assured', None):
                    premium_payment.calculate_premium()
                    premium_payment._original_sum_assured = instance.sum_assured
                    premium_payment.save()
            
            # Create Underwriting record for pending policies
            if instance.status == 'Pending':
                Underwriting.objects.get_or_create(
                    policy_holder=instance,
                    defaults={
                        'risk_assessment': 'Pending',
                        'medical_assessment': 'Pending'
                    }
                )

    except Exception as e:
        print(f"Error in policy_holder_post_save signal: {str(e)}")

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

@receiver(post_save, sender=PremiumPayment)
def update_agent_report(sender, instance, **kwargs):
    """
    Update or create AgentReport based on PremiumPayment updates
    """
    try:
        # Check if policy holder has an assigned agent
        if not instance.policy_holder.agent:
            return

        agent = instance.policy_holder.agent
        
        # Get or create agent report
        report, created = AgentReport.objects.get_or_create(
            agent=agent,
            company=agent.company,
            report_date=instance.next_payment_date,
            defaults={
                'policies_sold': 0,
                'total_premium': Decimal('0.00'),
                'commission_earned': Decimal('0.00'),
            }
        )

        # Update report statistics
        report.total_premium += instance.interval_payment
        report.policies_sold = report.policies_sold + 1 if created else report.policies_sold
        report.commission_earned += (instance.interval_payment * agent.commission_rate / 100)
        report.save()

    except Exception as e:
        print(f"Error in update_agent_report signal: {str(e)}")

@receiver(post_save, sender=AgentApplication)
def agent_application_approval(sender, instance, created, **kwargs):
    """
    Create SalesAgent when application is approved
    """
    try:
        if instance.status == "Approved" and not hasattr(instance, 'sales_agent'):
            agent_code = f"A-{instance.company.id}-{instance.branch.id}-{str(instance.id).zfill(4)}"
            
            SalesAgent.objects.create(
                company=instance.company,
                branch=instance.branch,
                application=instance,
                agent_code=agent_code,
                commission_rate=Decimal('5.00')  # Default commission rate
            )
    except Exception as e:
        print(f"Error in agent_application_approval signal: {str(e)}")

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
        
@receiver(post_save, sender=PolicyHolder)
def trigger_bonus_on_anniversary(sender, instance, **kwargs):
    """Trigger bonus calculation on policyholder's anniversary."""
    today = date.today()
    if instance.start_date.month == today.month and instance.start_date.day == today.day:
        # Create a bonus record for the policyholder
        Bonus.objects.create(
            policy_holder=instance,
            bonus_type='SI',  # Assuming Simple Interest as default
            start_date=today
        )


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
    if created:
        ClaimProcessing.objects.create(
            company=instance.company,
            claim_request=instance
        )
# automatically mark the paid onece the payment  is approved
@receiver(post_save, sender=ClaimProcessing)
def auto_finalize_payment(sender, instance, **kwargs):
    if instance.processing_status == 'Approved':
        PaymentProcessing.objects.filter(claim_request=instance.claim_request).update(
            processing_status='Completed'
        )
