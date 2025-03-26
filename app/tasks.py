from celery import shared_task
from django.db import transaction
from datetime import datetime, timedelta
from django.utils import timezone
from app.models import UserProfile, PremiumPayment, Policy, Loan, PolicyHolder
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_premium_payments():
    """
    Process premium payments that are due today.
    """
    try:
        with transaction.atomic():
            today = timezone.now().date()
            due_payments = PremiumPayment.objects.filter(due_date=today, status='PENDING')
            
            for payment in due_payments:
                payment.process_payment()
                logger.info(f"Processed payment for policy {payment.policy.id}")
    except Exception as e:
        logger.error(f"Error processing premium payments: {str(e)}")

@shared_task
def calculate_loan_interest():
    """
    Calculate interest for all active loans.
    """
    try:
        with transaction.atomic():
            active_loans = Loan.objects.filter(status='ACTIVE')
            
            for loan in active_loans:
                loan.apply_interest()
                logger.info(f"Applied interest to loan {loan.id}")
    except Exception as e:
        logger.error(f"Error calculating loan interest: {str(e)}")

@shared_task
def check_policy_anniversaries():
    """
    Check for policy anniversaries and apply bonuses if eligible.
    """
    try:
        with transaction.atomic():
            today = timezone.now().date()
            
            # Find policies with anniversary today
            policies = Policy.objects.filter(
                start_date__month=today.month,
                start_date__day=today.day,
                status='ACTIVE'
            )
            
            for policy in policies:
                years_active = today.year - policy.start_date.year
                if years_active > 0:
                    policy.apply_annual_bonus(years_active)
                    logger.info(f"Applied anniversary bonus for policy {policy.id}, years: {years_active}")
    except Exception as e:
        logger.error(f"Error checking policy anniversaries: {str(e)}")

@shared_task
def check_policy_expirations():
    """
    Check for policies that are expiring soon.
    """
    try:
        with transaction.atomic():
            today = timezone.now().date()
            expiration_window = today + timedelta(days=30)  # 30 days from now
            
            # Find policies expiring within the window
            soon_expiring = Policy.objects.filter(
                end_date__lte=expiration_window,
                end_date__gte=today,
                status='ACTIVE'
            )
            
            for policy in soon_expiring:
                # Send notification logic would go here
                logger.info(f"Policy {policy.id} expires on {policy.end_date}")
    except Exception as e:
        logger.error(f"Error checking policy expirations: {str(e)}")

@shared_task
def send_payment_reminders():
    """
    Send reminders for upcoming premium payments.
    """
    try:
        with transaction.atomic():
            today = timezone.now().date()
            reminder_date = today + timedelta(days=7)  # 7 days before due date
            
            # Find payments due in 7 days
            upcoming_payments = PremiumPayment.objects.filter(
                due_date=reminder_date,
                status='PENDING'
            )
            
            for payment in upcoming_payments:
                # Send reminder notification logic would go here
                logger.info(f"Reminder sent for payment due on {payment.due_date} for policy {payment.policy.id}")
    except Exception as e:
        logger.error(f"Error sending payment reminders: {str(e)}")