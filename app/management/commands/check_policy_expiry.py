from django.core.management.base import BaseCommand
from datetime import date, timedelta
from django.db.models import Q, Max, F
from app.models import PremiumPayment, PolicyHolder
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check policies for expiry due to non-payment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force check all policies regardless of due date',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1200,  # Approximately 3 years + 3 months to capture all potential expiries
            help='Only check policies active within the last N days (default: 1200)',
        )

    def handle(self, *args, **options):
        force_check = options['force']
        days_limit = options['days']
        today = date.today()
        cutoff_date = today - timedelta(days=days_limit)
        
        self.stdout.write('Checking for expired policies...')
        
        # Get active policies with start dates within the time limit
        active_policies = PolicyHolder.objects.filter(
            ~Q(status='Expired') & ~Q(status='Surrendered'),
            start_date__gte=cutoff_date
        )
        
        self.stdout.write(f'Found {active_policies.count()} policies to check from the last {days_limit} days')
        
        # Filter policies with unpaid premiums
        unpaid_premiums = PremiumPayment.objects.filter(
            policy_holder__in=active_policies,
            payment_status__in=['Unpaid', 'Partially Paid']
        ).select_related('policy_holder')
        
        checked_count = 0
        expired_count = 0

        # First check for policies with missing payments based on start date
        for policy in active_policies:
            # Skip policies without premium payments (they'll be handled elsewhere)
            if not policy.premium_payments.exists():
                continue
                
            # Get the last payment record and date
            last_payment = policy.premium_payments.aggregate(
                last_date=Max('next_payment_date')
            )['last_date']
            
            # Skip if no payment date is recorded
            if not last_payment:
                continue
                
            # Calculate days since last payment date
            days_late = (today - last_payment).days
            
            # Check if policy has been non-paying for more than 3 years
            if days_late > 1095 or force_check:
                checked_count += 1
                
                # Mark as expired if meets criteria
                if days_late > 1095:
                    policy.status = 'Expired'
                    policy.save(update_fields=['status'])
                    
                    # Also update all related premium payments
                    policy.premium_payments.filter(
                        payment_status__in=['Unpaid', 'Partially Paid']
                    ).update(payment_status='Expired')
                    
                    expired_count += 1
                    logger.info(f"Policy {policy.id} marked as expired due to no payments for {days_late} days")
        
        # Then check all unpaid premiums with next_payment_date
        for payment in unpaid_premiums:
            if not payment.next_payment_date:
                continue
                
            days_late = (today - payment.next_payment_date).days
            
            # Check policies with payments due more than 3 years ago, or check all with force
            if days_late > 1095 or force_check:
                checked_count += 1
                
                # Skip policies already marked as expired above
                if payment.policy_holder.status == 'Expired':
                    continue
                    
                if payment.check_policy_expiry():
                    # Save the payment to persist the 'Expired' status after check_policy_expiry
                    payment.save(update_fields=['payment_status'])
                    expired_count += 1
                    logger.info(f"Policy {payment.policy_holder.id} marked as expired due to non-payment for {days_late} days")
        
        self.stdout.write(self.style.SUCCESS(f'Finished checking {checked_count} policies. {expired_count} policies marked as expired.')) 