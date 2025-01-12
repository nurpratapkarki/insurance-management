from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from decimal import Decimal
from datetime import date
from .models import (
    PolicyHolder, 
    Underwriting, 
    PremiumPayment, 
    InsurancePolicy, 
    AgentReport, 
    AgentApplication, 
    SalesAgent
)

# 1. PolicyHolder Signals
@receiver(post_save, sender=PolicyHolder)
def policy_holder_changes(sender, instance, created, **kwargs):
    """
    Handle all PolicyHolder-related updates in one signal
    """
    if instance.status == "Approved":
        # Create or update underwriting
        underwriting, _ = Underwriting.objects.get_or_create(policy_holder=instance)
        underwriting.save()  # This triggers risk recalculation
        
        # Create initial premium payment if new
        if created:
            PremiumPayment.objects.create(policy_holder=instance)
            
        # Update existing premium payments
        for payment in instance.premium_payments.all():
            payment.save()  # This triggers premium recalculation

# 2. Underwriting Signal
@receiver(post_save, sender=Underwriting)
def underwriting_changes(sender, instance, **kwargs):
    """
    Update premium payments when underwriting changes
    """
    for payment in instance.policy_holder.premium_payments.all():
        payment.save()  # Triggers premium recalculation

# 3. Insurance Policy Signal
@receiver(post_save, sender=InsurancePolicy)
def policy_changes(sender, instance, **kwargs):
    """
    Update all related premium payments when policy terms change
    """
    for policy_holder in instance.policy_holders.all():
        for payment in policy_holder.premium_payments.all():
            payment.save()  # Triggers premium recalculation

# 4. Premium Payment Signal
@receiver(post_save, sender=PremiumPayment)
def premium_payment_changes(sender, instance, created, **kwargs):
    """
    Handle premium payment updates and agent report updates
    """
    if created:
        # Update agent report
        agent = instance.policy_holder.agent
        if agent:
            report, created = AgentReport.objects.get_or_create(
                agent=agent,
                company=agent.company,
                report_date=date.today(),
                defaults={
                    'reporting_period': 'Daily',
                    'policies_sold': 0,
                    'total_premium': Decimal('0.00'),
                    'commission_earned': Decimal('0.00'),
                    'target_achievement': Decimal('0.00'),
                    'renewal_rate': Decimal('0.00'),
                    'customer_retention': Decimal('0.00')
                }
            )
            
            # Update report metrics
            report.total_premium += instance.interval_payment
            report.policies_sold += 1
            report.commission_earned += instance.interval_payment * agent.commission_rate / Decimal('100')
            report.save()

# 5. Agent Application Signal
@receiver(post_save, sender=AgentApplication)
def agent_application_approval(sender, instance, **kwargs):
    """
    Create SalesAgent when application is approved
    """
    if instance.status == "Approved" and not hasattr(instance, 'sales_agent'):
        SalesAgent.objects.create(
            company=instance.company,
            branch=instance.branch,
            application=instance,
            agent_code=f"A-{instance.company.id}-{instance.branch.id}-{str(instance.id).zfill(4)}",
            commission_rate=5.00  # Default commission rate
        )

# 6. PolicyHolder Cleanup Signal
@receiver(pre_delete, sender=PolicyHolder)
def cleanup_policy_holder_data(sender, instance, **kwargs):
    """
    Clean up related data when a PolicyHolder is deleted
    """
    Underwriting.objects.filter(policy_holder=instance).delete()
    PremiumPayment.objects.filter(policy_holder=instance).delete()