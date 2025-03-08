from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import OTP, PolicyHolder, SalesAgent

import random
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def mobile_login(request):
    """Login via phone number (username) and password"""
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')
    
    if not phone_number or not password:
        return Response({'error': 'Phone number and password are required'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Use phone number as username
    user = authenticate(username=phone_number, password=password)
    
    if not user:
        return Response({'error': 'Invalid credentials'}, 
                        status=status.HTTP_401_UNAUTHORIZED)
    
    # Determine if user is policy holder or agent
    user_type = None
    user_data = {}
    
    try:
        if hasattr(user, 'policy_holder') and user.policy_holder:
            user_type = 'policy_holder'
            policy_holder = user.policy_holder
            user_data = {
                'id': policy_holder.id,
                'name': f"{policy_holder.first_name} {policy_holder.last_name}",
                'policy_number': policy_holder.policy_number,
                'phone_number': policy_holder.phone_number,
                'email': policy_holder.email,
            }
        elif hasattr(user, 'sales_agent') and user.sales_agent:
            user_type = 'agent'
            agent = user.sales_agent
            user_data = {
                'id': agent.id,
                'name': agent.get_full_name(),
                'agent_code': agent.agent_code,
                'phone_number': agent.phone_number,
                'email': agent.email,
            }
    except Exception as e:
        logger.error(f"Error determining user type: {str(e)}")
    
    login(request, user)
    
    return Response({
        'message': 'Login successful',
        'user_id': user.id,
        'user_type': user_type,
        'user_data': user_data,
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_otp(request):
    """Generate OTP for password reset"""
    phone_number = request.data.get('phone_number')
    
    if not phone_number:
        return Response({'error': 'Phone number is required'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Find user by phone number
    try:
        # Check both policy holders and agents
        user = User.objects.filter(username=phone_number).first()
        
        if not user:
            # Also check policy holder or agent phone number fields directly
            policy_holder = PolicyHolder.objects.filter(phone_number=phone_number).first()
            agent = SalesAgent.objects.filter(phone_number=phone_number).first()
            
            if policy_holder and policy_holder.user:
                user = policy_holder.user
            elif agent and agent.user:
                user = agent.user
            else:
                return Response({'error': 'No user found with this phone number'}, 
                                status=status.HTTP_404_NOT_FOUND)
        
        # Generate OTP
        otp = OTP.generate_otp(user)
        
        # In production, send OTP via SMS
        # For now, we'll return it in the response (for testing only)
        return Response({
            'message': 'OTP generated successfully',
            'otp': otp.otp,  # Remove this in production
            'expires_at': otp.expires_at,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating OTP: {str(e)}")
        return Response({'error': 'Failed to generate OTP'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP and reset password"""
    phone_number = request.data.get('phone_number')
    otp_code = request.data.get('otp')
    new_password = request.data.get('new_password')
    
    if not phone_number or not otp_code or not new_password:
        return Response({
            'error': 'Phone number, OTP and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find user by phone number
        user = User.objects.filter(username=phone_number).first()
        
        if not user:
            # Also check policy holder or agent phone number fields directly
            policy_holder = PolicyHolder.objects.filter(phone_number=phone_number).first()
            agent = SalesAgent.objects.filter(phone_number=phone_number).first()
            
            if policy_holder and policy_holder.user:
                user = policy_holder.user
            elif agent and agent.user:
                user = agent.user
            else:
                return Response({'error': 'No user found with this phone number'}, 
                                status=status.HTTP_404_NOT_FOUND)
        
        # Find valid OTP for this user
        otp = OTP.objects.filter(
            user=user,
            otp=otp_code,
            is_used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at').first()
        
        if not otp:
            return Response({'error': 'Invalid or expired OTP'}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Mark OTP as used
        otp.is_used = True
        otp.save()
        
        # Reset password
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password reset successful'}, 
                        status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        return Response({'error': 'Failed to verify OTP'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password for logged in user"""
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response({
            'error': 'Current password and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    # Verify current password
    if not user.check_password(current_password):
        return Response({'error': 'Current password is incorrect'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Change password
    user.set_password(new_password)
    user.save()
    
    return Response({'message': 'Password changed successfully'}, 
                    status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_logout(request):
    """Log out the user"""
    logout(request)
    return Response({'message': 'Logged out successfully'}, 
                    status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """Get the profile of the logged-in user"""
    user = request.user
    profile_data = {
        'user_id': user.id,
        'username': user.username,
    }
    
    try:
        # Check if user is a policy holder
        if hasattr(user, 'policy_holder') and user.policy_holder:
            policy_holder = user.policy_holder
            profile_data.update({
                'user_type': 'policy_holder',
                'id': policy_holder.id,
                'first_name': policy_holder.first_name,
                'last_name': policy_holder.last_name,
                'policy_number': policy_holder.policy_number,
                'phone_number': policy_holder.phone_number,
                'email': policy_holder.email,
                'date_of_birth': policy_holder.date_of_birth,
                'gender': policy_holder.gender,
            })
            
            # Add policy information if available
            if policy_holder.policy:
                profile_data['policy'] = {
                    'id': policy_holder.policy.id,
                    'name': policy_holder.policy.name,
                    'policy_type': policy_holder.policy.policy_type,
                    'sum_assured': str(policy_holder.sum_assured),
                    'start_date': policy_holder.start_date,
                    'maturity_date': policy_holder.maturity_date,
                }
            
            # Add payment information if available
            try:
                premium_payment = policy_holder.premium_payments.order_by('-id').first()
                if premium_payment:
                    profile_data['payment'] = {
                        'payment_status': premium_payment.payment_status,
                        'next_payment_date': premium_payment.next_payment_date,
                        'total_paid': str(premium_payment.total_paid),
                        'total_premium': str(premium_payment.total_premium),
                        'remaining_premium': str(premium_payment.remaining_premium),
                    }
            except Exception as e:
                logger.error(f"Error fetching payment data: {str(e)}")
            
        # Check if user is a sales agent
        elif hasattr(user, 'sales_agent') and user.sales_agent:
            agent = user.sales_agent
            profile_data.update({
                'user_type': 'agent',
                'id': agent.id,
                'name': agent.get_full_name(),
                'agent_code': agent.agent_code,
                'phone_number': agent.phone_number,
                'email': agent.email,
                'branch_name': agent.branch.name if agent.branch else None,
                'is_active': agent.is_active,
                'commission_rate': str(agent.commission_rate),
                'total_policies_sold': agent.total_policies_sold,
            })
            
            # Add performance metrics
            try:
                latest_report = agent.agenreport_set.order_by('-report_date').first()
                if latest_report:
                    profile_data['performance'] = {
                        'report_date': latest_report.report_date,
                        'policies_sold': latest_report.policies_sold,
                        'total_premium': str(latest_report.total_premium),
                        'commission_earned': str(latest_report.commission_earned),
                        'target_achievement': str(latest_report.target_achievement),
                    }
            except Exception as e:
                logger.error(f"Error fetching agent report: {str(e)}")
                
        return Response(profile_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return Response({'error': 'Failed to retrieve profile data'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_policy_holder_policies(request):
    """Get all policies for the logged-in policy holder"""
    user = request.user
    
    if not hasattr(user, 'policy_holder') or not user.policy_holder:
        return Response({'error': 'User is not a policy holder'}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    policy_holder = user.policy_holder
    policy_data = {}
    
    try:
        policy = policy_holder.policy
        if policy:
            policy_data = {
                'id': policy.id,
                'name': policy.name,
                'policy_type': policy.policy_type,
                'sum_assured': str(policy_holder.sum_assured),
                'start_date': policy_holder.start_date,
                'maturity_date': policy_holder.maturity_date,
                'duration_years': policy_holder.duration_years,
                'include_adb': policy_holder.include_adb,
                'include_ptd': policy_holder.include_ptd,
                'payment_interval': policy_holder.payment_interval,
                'payment_status': policy_holder.payment_status,
            }
        
        return Response(policy_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting policy holder policies: {str(e)}")
        return Response({'error': 'Failed to retrieve policy data'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_agent_clients(request):
    """Get all clients (policy holders) for the logged-in agent"""
    user = request.user
    
    if not hasattr(user, 'sales_agent') or not user.sales_agent:
        return Response({'error': 'User is not a sales agent'}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    agent = user.sales_agent
    
    try:
        policy_holders = PolicyHolder.objects.filter(agent=agent)
        
        clients_data = []
        for ph in policy_holders:
            client = {
                'id': ph.id,
                'name': f"{ph.first_name} {ph.last_name}",
                'policy_number': ph.policy_number,
                'policy_name': ph.policy.name if ph.policy else None,
                'sum_assured': str(ph.sum_assured) if ph.sum_assured else None,
                'start_date': ph.start_date,
                'status': ph.status,
            }
            clients_data.append(client)
        
        return Response(clients_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting agent clients: {str(e)}")
        return Response({'error': 'Failed to retrieve client data'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)