from celery import shared_task
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import F, Q
import logging

from .models import PremiumPayment, Loan, PolicyHolder, Bonus

logger = logging.getLogger(__name__)

@shared_task
def apply_premium_fines():
    """Apply fines to overdue premium payments (runs daily)"""
    today = date.today()
    grace_period_days = 15  # Configurable grace period
    
    overdue_payments = PremiumPayment.objects.filter(
        payment_status__in=['Due', 'Partially Paid'],
        next_payment_date__lt=today - timedelta(days=grace_period_days)
    ).select_for_update(skip_locked=True)
    
    processed_count = 0
    error_count = 0
    
    for payment in overdue_payments:
        try:
            with transaction.atomic():
                # Get fresh instance to avoid race conditions
                payment_obj = PremiumPayment.objects.select_for_update().get(id=payment.id)
                
                # Calculate fine (e.g., 1% of interval payment per day overdue)
                days_overdue = (today - (payment_obj.next_payment_date + timedelta(days=grace_period_days))).days
                if days_overdue <= 0:
                    continue
                    
                fine_rate = Decimal('0.01')  # 1% per day
                fine_amount = payment_obj.interval_payment * fine_rate * Decimal(days_overdue)
                fine_amount = min(fine_amount, payment_obj.interval_payment * Decimal('0.50'))  # Cap at 50%
                
                # Apply fine only if it hasn't been applied yet for this period
                if payment_obj.fine_due == 0:
                    payment_obj.fine_due = fine_amount
                    payment_obj.save(update_fields=['fine_due'])
                    
                    # Log the fine application
                    logger.info(f"Applied fine of {fine_amount} to payment {payment_obj.id} for policy holder {payment_obj.policy_holder.id}")
                    
                processed_count += 1
                
        except Exception as e:
            logger.error(f"Error applying fine for payment {payment.id}: {str(e)}")
            error_count += 1
    
    return f"Processed {processed_count} payments, {error_count} errors"

@shared_task
def accrue_loan_interest():
    """Daily task to accrue interest on active loans"""
    active_loans = Loan.objects.filter(loan_status='Active').select_for_update(skip_locked=True)
    
    processed_count = 0
    error_count = 0
    
    for loan in active_loans:
        try:
            with transaction.atomic():
                # Get fresh instance
                loan_obj = Loan.objects.select_for_update().get(id=loan.id)
                loan_obj.accrue_interest()
                processed_count += 1
                
        except Exception as e:
            logger.error(f"Error accruing interest for loan {loan.id}: {str(e)}")
            error_count += 1
    
    return f"Processed {processed_count} loans, {error_count} errors"

@shared_task
def check_policy_anniversaries():
    """Check and process policy anniversaries for bonus calculations"""
    today = date.today()
    
    # Find policies with anniversary today
    anniversary_policies = PolicyHolder.objects.filter(
        status='Active',
        start_date__month=today.month,
        start_date__day=today.day
    ).select_for_update(skip_locked=True)
    
    processed_count = 0
    error_count = 0
    
    for policy in anniversary_policies:
        try:
            with transaction.atomic():
                # Check if bonus already exists for this year
                if not Bonus.objects.filter(
                    policy_holder=policy,
                    start_date__year=today.year
                ).exists():
                    Bonus.objects.create(
                        policy_holder=policy,
                        start_date=today
                    )
                    processed_count += 1
                    
        except Exception as e:
            logger.error(f"Error processing anniversary for policy {policy.id}: {str(e)}")
            error_count += 1
    
    return f"Processed {processed_count} policy anniversaries, {error_count} errors"

@shared_task
def check_policy_expiration():
    """Check for policies that are expiring soon and need renewal notices"""
    today = date.today()
    notice_days = [30, 15, 7, 1]  # Days before expiry to send notices
    
    for days in notice_days:
        expiring_date = today + timedelta(days=days)
        expiring_policies = PolicyHolder.objects.filter(
            status='Active',
            maturity_date=expiring_date
        )
        
        for policy in expiring_policies:
            # Here you would trigger notification logic
            logger.info(f"Policy {policy.id} expires in {days} days")
    
    # Also handle expired policies
    expired_policies = PolicyHolder.objects.filter(
        status='Active',
        maturity_date__lt=today
    )
    
    for policy in expired_policies:
        policy.status = 'Expired'
        policy.save(update_fields=['status'])
        logger.info(f"Policy {policy.id} marked as expired")

@shared_task
def send_payment_reminders():
    """Send reminders for upcoming premium payments"""
    today = date.today()
    reminder_days = [15, 7, 3, 1]  # Days before payment to send reminders
    
    for days in reminder_days:
        reminder_date = today + timedelta(days=days)
        
        # Find payments due on the reminder date
        upcoming_payments = PremiumPayment.objects.filter(
            next_payment_date=reminder_date,
            payment_status__in=['Unpaid', 'Partially Paid']
        )
        
        for payment in upcoming_payments:
            try:
                policy_holder = payment.policy_holder
                
                # Check if reminder already sent for this date
                reminder_key = f"{reminder_date.isoformat()}-{days}"
                reminders_sent = payment.payment_reminders_sent or []
                
                if reminder_key not in reminders_sent:
                    # Here you would send the actual notification
                    # (email, SMS, push notification, etc.)
                    
                    # For now, just log it
                    logger.info(
                        f"Payment reminder: Policy {policy_holder.policy_number} "
                        f"has payment of {payment.interval_payment} due in {days} days"
                    )
                    
                    # Record that reminder was sent
                    reminders_sent.append(reminder_key)
                    payment.payment_reminders_sent = reminders_sent
                    payment.save(update_fields=['payment_reminders_sent'])
                    
            except Exception as e:
                logger.error(f"Error sending payment reminder: {str(e)}")
    
    # Also send reminders for overdue payments
    overdue_payments = PremiumPayment.objects.filter(
        next_payment_date__lt=today,
        payment_status__in=['Unpaid', 'Partially Paid', 'Overdue']
    )
    
    for payment in overdue_payments:
        try:
            policy_holder = payment.policy_holder
            days_overdue = (today - payment.next_payment_date).days
            
            # Send reminders at different intervals for overdue payments
            if days_overdue in [1, 5, 10, 15, 30, 60, 90]:
                reminder_key = f"overdue-{today.isoformat()}-{days_overdue}"
                reminders_sent = payment.payment_reminders_sent or []
                
                if reminder_key not in reminders_sent:
                    # Log the overdue reminder
                    logger.info(
                        f"Overdue payment reminder: Policy {policy_holder.policy_number} "
                        f"has payment of {payment.interval_payment} overdue by {days_overdue} days"
                    )
                    
                    # Record that reminder was sent
                    reminders_sent.append(reminder_key)
                    payment.payment_reminders_sent = reminders_sent
                    payment.save(update_fields=['payment_reminders_sent'])
        
        except Exception as e:
            logger.error(f"Error sending overdue payment reminder: {str(e)}")
    
    return "Payment reminders processed"