from django.core.management.base import BaseCommand
from datetime import date
from django.db.models import Q
from app.models import PolicyHolder, Bonus
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update bonus accruals for all active policies on their anniversaries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Check all policies regardless of anniversary date',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Check policies with anniversaries within this many days (default: 30)',
        )

    def handle(self, *args, **options):
        check_all = options['all']
        days_window = options['days']
        today = date.today()
        
        self.stdout.write('Checking for policy anniversaries to add bonuses...')
        
        # Get all active endowment policies 
        active_policies = PolicyHolder.objects.filter(
            status='Active',
            policy__policy_type='Endowment'
        )
        
        if not check_all:
            # Only check policies with recent or upcoming anniversaries
            month_policies = []
            for policy in active_policies:
                # Calculate anniversary date for current year
                anniversary_date = date(today.year, policy.start_date.month, policy.start_date.day)
                
                # If anniversary already passed this year, calculate days since
                if anniversary_date < today:
                    days_diff = (today - anniversary_date).days
                    if days_diff <= days_window:
                        month_policies.append(policy.id)
                else:
                    # If anniversary is upcoming, calculate days until
                    days_diff = (anniversary_date - today).days
                    if days_diff <= days_window:
                        month_policies.append(policy.id)
            
            # Filter to only policies with anniversaries in the window
            active_policies = active_policies.filter(id__in=month_policies)
        
        self.stdout.write(f'Found {active_policies.count()} active endowment policies to check')
        
        processed_count = 0
        bonus_added_count = 0
        
        for policy in active_policies:
            # Get or create bonus record
            bonus, created = Bonus.objects.get_or_create(
                policy_holder=policy,
                defaults={'start_date': policy.start_date}
            )
            
            # Check for anniversary and add bonus if needed
            bonus_added = bonus.update_anniversary_bonus()
            
            processed_count += 1
            if bonus_added:
                bonus_added_count += 1
                
            # Log progress for large datasets
            if processed_count % 100 == 0:
                self.stdout.write(f'Processed {processed_count} policies so far...')
        
        self.stdout.write(self.style.SUCCESS(
            f'Processed {processed_count} policies. Added bonuses for {bonus_added_count} policy anniversaries.'
        )) 