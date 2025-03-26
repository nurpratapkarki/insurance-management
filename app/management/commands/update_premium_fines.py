from django.core.management.base import BaseCommand
from datetime import date, timedelta
from django.db.models import Q
from app.models import PremiumPayment, PolicyHolder
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update fine calculations for premium payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update all premium payments, including those with paid status',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Only check policies active within the last N days (default: 365)',
        )

    def handle(self, *args, **options):
        update_all = options['all']
        days_limit = options['days']
        today = date.today()
        cutoff_date = today - timedelta(days=days_limit)
        
        self.stdout.write('Updating fine calculations for premium payments...')
        
        # Get active policies with start dates within the time limit
        active_policies = PolicyHolder.objects.filter(
            Q(status='Active') | Q(status='Pending'),
            start_date__gte=cutoff_date
        )
        
        self.stdout.write(f'Found {active_policies.count()} active policies within the last {days_limit} days')
        
        # Filter premium payments based on active policies
        if update_all:
            premium_payments = PremiumPayment.objects.filter(
                policy_holder__in=active_policies
            )
        else:
            premium_payments = PremiumPayment.objects.filter(
                policy_holder__in=active_policies
            ).exclude(payment_status='Paid')
            
        updated_count = 0
        fines_added = 0
        
        for payment in premium_payments:
            # Update next payment date if it's not set
            if not payment.next_payment_date:
                interval_months = {
                    "quarterly": 3,
                    "semi_annual": 6,
                    "annual": 12,
                    "Single": None
                }.get(payment.policy_holder.payment_interval)
                
                if interval_months:
                    policy_start = payment.policy_holder.start_date
                    # Set next payment date based on policy start date
                    payment.next_payment_date = policy_start.replace(
                        month=((policy_start.month - 1 + interval_months) % 12) + 1,
                        year=policy_start.year + ((policy_start.month - 1 + interval_months) // 12)
                    )
                    logger.info(f"Set next payment date for policy {payment.policy_holder.id} to {payment.next_payment_date}")
            
            # Calculate current fine
            current_fine = payment.calculate_fine()
            
            # Update if there's a fine to add
            if current_fine > 0:
                old_fine = payment.fine_due
                payment.fine_due = current_fine
                payment.save(update_fields=['fine_due', 'next_payment_date'])
                
                fines_added += 1
                logger.info(f"Updated fine for {payment.policy_holder.id} from {old_fine} to {current_fine}")
            elif payment.next_payment_date and payment.next_payment_date != payment.next_payment_date:
                # Save if only the next payment date was updated
                payment.save(update_fields=['next_payment_date'])
            
            updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Updated {updated_count} premium payments. Added/updated fines for {fines_added} payments.'
        )) 