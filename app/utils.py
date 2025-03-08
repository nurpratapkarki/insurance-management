import json
import logging
from datetime import datetime
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str

logger = logging.getLogger(__name__)

def log_audit(user, obj, action_flag, change_message=''):
    """
    Create an admin log entry for auditing purposes.
    
    Args:
        user: The user performing the action
        obj: The model instance being affected
        action_flag: ADDITION, CHANGE, or DELETION
        change_message: Description of the change
    """
    try:
        LogEntry.objects.log_action(
            user_id=user.id,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.pk,
            object_repr=force_str(obj),
            action_flag=action_flag,
            change_message=change_message
        )
    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}")

def log_financial_transaction(transaction_type, user, amount, related_object, details=None):
    """
    Log a financial transaction for audit purposes.
    
    Args:
        transaction_type: Type of transaction (payment, claim, loan, etc.)
        user: User who performed the transaction
        amount: Decimal amount of the transaction
        related_object: The model instance related to the transaction
        details: Additional details as a dictionary
    """
    try:
        details = details or {}
        
        log_data = {
            'transaction_type': transaction_type,
            'user': user.username,
            'user_id': user.id,
            'amount': str(amount),
            'timestamp': datetime.now().isoformat(),
            'object_type': related_object.__class__.__name__,
            'object_id': related_object.pk,
            'details': details
        }
        
        # Log to file
        logger.info(f"FINANCIAL_TRANSACTION: {json.dumps(log_data)}")
        
        # Create admin log entry
        message = f"Financial transaction: {transaction_type} of {amount} for {related_object}"
        log_audit(user, related_object, CHANGE, message)
        
    except Exception as e:
        logger.error(f"Error logging financial transaction: {str(e)}")

def log_policy_state_change(policy_holder, old_status, new_status, user, reason=None):
    """
    Log a policy state change for audit purposes.
    
    Args:
        policy_holder: The PolicyHolder instance
        old_status: Previous status
        new_status: New status
        user: User who made the change
        reason: Reason for the status change
    """
    try:
        log_data = {
            'policy_number': policy_holder.policy_number,
            'policy_holder_id': policy_holder.id,
            'old_status': old_status,
            'new_status': new_status,
            'user': user.username,
            'user_id': user.id,
            'timestamp': datetime.now().isoformat(),
            'reason': reason or 'Not specified'
        }
        
        # Log to file
        logger.info(f"POLICY_STATE_CHANGE: {json.dumps(log_data)}")
        
        # Create admin log entry
        message = f"Policy status changed from {old_status} to {new_status}. Reason: {reason or 'Not specified'}"
        log_audit(user, policy_holder, CHANGE, message)
        
    except Exception as e:
        logger.error(f"Error logging policy state change: {str(e)}")

def log_claim_processing(claim, old_status, new_status, user, remarks=None):
    """
    Log claim processing activity for audit purposes.
    
    Args:
        claim: The ClaimRequest instance
        old_status: Previous status
        new_status: New status
        user: User who processed the claim
        remarks: Processing remarks
    """
    try:
        policy_holder = claim.policy_holder
        
        log_data = {
            'claim_id': claim.id,
            'policy_number': policy_holder.policy_number,
            'policy_holder_id': policy_holder.id,
            'old_status': old_status,
            'new_status': new_status,
            'user': user.username,
            'user_id': user.id,
            'timestamp': datetime.now().isoformat(),
            'remarks': remarks or 'No remarks',
            'claim_amount': str(claim.claim_amount)
        }
        
        # Log to file
        logger.info(f"CLAIM_PROCESSING: {json.dumps(log_data)}")
        
        # Create admin log entry
        message = f"Claim status changed from {old_status} to {new_status}. Remarks: {remarks or 'No remarks'}"
        log_audit(user, claim, CHANGE, message)
        
    except Exception as e:
        logger.error(f"Error logging claim processing: {str(e)}")

def log_system_event(event_type, description, related_object=None, severity='INFO'):
    """
    Log a system event for monitoring and troubleshooting.
    
    Args:
        event_type: Type of system event
        description: Description of the event
        related_object: Optional related model instance
        severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        log_data = {
            'event_type': event_type,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'severity': severity
        }
        
        if related_object:
            log_data.update({
                'object_type': related_object.__class__.__name__,
                'object_id': related_object.pk
            })
        
        # Log based on severity
        log_method = getattr(logger, severity.lower(), logger.info)
        log_method(f"SYSTEM_EVENT: {json.dumps(log_data)}")
        
    except Exception as e:
        logger.error(f"Error logging system event: {str(e)}") 