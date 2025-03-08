import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insurance-management.settings')

app = Celery('insurance-management')

# Use string names for configuration to avoid pickle issues
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

# Configure the periodic tasks
app.conf.beat_schedule = {
    'apply-premium-fines-daily': {
        'task': 'app.tasks.apply_premium_fines',
        'schedule': crontab(hour=0, minute=0),  # Run at midnight every day
    },
    'accrue-loan-interest-daily': {
        'task': 'app.tasks.accrue_loan_interest',
        'schedule': crontab(hour=1, minute=0),  # Run at 1 AM every day
    },
    'check-policy-anniversaries': {
        'task': 'app.tasks.check_policy_anniversaries',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM every day
    },
    'check-policy-expiration': {
        'task': 'app.tasks.check_policy_expiration',
        'schedule': crontab(hour=3, minute=0),  # Run at 3 AM every day
    },
    'send-payment-reminders': {
        'task': 'app.tasks.send_payment_reminders',
        'schedule': crontab(hour=9, minute=0),  # Run at 9 AM every day
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 