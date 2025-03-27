from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        """Import signals when the app is ready to ensure they are connected."""
        import app.signals  # noqa
        
        # Only run in actual server environment (not during migrations or other Django commands)
        import os
        if os.environ.get('RUN_MAIN', None) != 'true':
            return
            
        # Import and run premium system updates
        try:
            from django.core.management import call_command
            
            logger.info("Running automatic premium system updates on server startup")
            
            # Update premium fines
            logger.info("Updating premium fines...")
            call_command('update_premium_fines')
            
            # Check for policy expiry
            logger.info("Checking policy expiry status...")
            call_command('check_policy_expiry')
            
            # Update policy bonuses on anniversaries
            logger.info("Updating policy bonuses...")
            call_command('update_bonuses')
            
            logger.info("Automatic premium system updates completed")
        except Exception as e:
            logger.error(f"Error running premium system updates: {str(e)}")