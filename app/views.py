from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.contrib import messages
from datetime import datetime
from django.core.exceptions import ValidationError
from .serializers import *
from .models import *
from .frontend_data import Dashboard, MortalityRateGeneratorForm, MortalityRateBulkForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin import site


def handle_image_update(instance, field_name, request_data):
    if field_name in request_data:
        if request_data[field_name] not in [None, '', 'null']:
            setattr(instance, field_name, request_data[field_name])
    return instance
# Helper function to check permissions and filter data by company
def check_permissions_and_filter(request, queryset=None):
    # Checks permissions and optionally filters queryset by the user's company.
    if request.user.is_superuser:
        return queryset if queryset else True  # Superuser has unrestricted access
    if queryset:
        return queryset.filter(company=request.user.company)  # Filter data by company
    return True

# Generic response handler
def handle_serializer(serializer, success_status=status.HTTP_200_OK):
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=success_status)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def insuranceHome(request):
    company = request.user.company
    data = {
        "insurancePolicies": InsurancePolicySerializer(
            InsurancePolicy.objects.filter(company=company).select_related('company'), 
            many=True
        ).data,
        "policyHolders": PolicyHolderSerializer(
            PolicyHolder.objects.filter(company=company)
            .select_related('agent', 'policy', 'branch', 'company'), 
            many=True
        ).data,
        "claims": ClaimRequestSerializer(
            ClaimRequest.objects.filter(company=company)
            .select_related('policy_holder', 'company'), 
            many=True
        ).data,
        "salesAgents": SalesAgentSerializer(
            SalesAgent.objects.filter(company=company)
            .select_related('company'), 
            many=True
        ).data,
        "branches": BranchSerializer(
            Branch.objects.filter(company=company), 
            many=True
        ).data,
    }
    return Response(data)


# Insurance Policy Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllPolicies(request):
    policies = InsurancePolicy.objects.filter(company=request.user.company).select_related('company')
    return Response(InsurancePolicySerializer(policies, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createPolicy(request):
    data = request.data.copy()
    if not request.user.is_superuser:
        data['company'] = request.user.company.id  # Automatically assign company for non-superusers
    serializer = InsurancePolicySerializer(data=data)
    return handle_serializer(serializer, success_status=status.HTTP_201_CREATED)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def policyDetails(request, id):
    if request.user.is_superuser:
        policy = get_object_or_404(InsurancePolicy, id=id)
    else:
        policy = get_object_or_404(
        InsurancePolicy.objects.filter(company=request.user.company), 
        id=id
    )

    return Response(InsurancePolicySerializer(policy).data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updatePolicy(request, id):
    policy = get_object_or_404(InsurancePolicy, id=id, company=request.user.company)
    serializer = InsurancePolicySerializer(policy, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deletePolicy(request, id):
    policy = get_object_or_404(InsurancePolicy, id=id, company=request.user.company)
    policy.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# Policy Holder Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllPolicyHolders(request):
    holders = PolicyHolder.objects.filter(company=request.user.company)\
        .select_related('agent', 'policy', 'branch', 'company')
    return Response(PolicyHolderSerializer(holders, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createPolicyHolder(request):
    data = request.data.copy()
    if not request.user.is_superuser:
        data['company'] = request.user.company.id  # Automatically assign company for non-superusers
    serializer = PolicyHolderSerializer(data=data)
    return handle_serializer(serializer, success_status=status.HTTP_201_CREATED)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def policyHolderDetails(request, id):
    try:
        # Retrieve the policy holder
        if request.user.is_superuser:
            holder = get_object_or_404(PolicyHolder, id=id)
        else:
            holder = get_object_or_404(
                PolicyHolder.objects.filter(company=request.user.company), id=id
            )

        # Perform premium calculations
        if holder.policy:
            premium_payment = PremiumPayment(policy_holder=holder)
            _, loaded_annual_premium, interval_payment = premium_payment.calculate_premium()

            response_data = PolicyHolderSerializer(holder).data
            response_data.update({
                "loaded_annual_premium": float(loaded_annual_premium),
                "interval_payment": float(interval_payment),
            })
            return Response(response_data)
        else:
            return Response({"error": "PolicyHolder has no associated policy."}, status=400)
    except PolicyHolder.DoesNotExist:
        return Response({"error": "PolicyHolder not found."}, status=404)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updatePolicyHolder(request, id):
    holder = get_object_or_404(PolicyHolder, id=id, company=request.user.company)
    
    try:
        image_fields = ['document_front', 'document_back', 'pp_photo', 
                       'nominee_document_front', 'nominee_document_back', 'nominee_pp_photo']
        
        for field in image_fields:
            holder = handle_image_update(holder, field, request.data)
        
        serializer = PolicyHolderSerializer(holder, data=request.data, partial=True)
        if serializer.is_valid():
            updated_holder = serializer.save()
            return Response(PolicyHolderSerializer(updated_holder).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deletePolicyHolder(request, id):
    holder = get_object_or_404(PolicyHolder, id=id, company=request.user.company)
    holder.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def policyHoldersByBranch(request, branchId):
    holders = PolicyHolder.objects.filter(branch_id=branchId)
    return Response(PolicyHolderSerializer(holders, many=True).data)

# Claims Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllClaims(request):
    claims = ClaimRequest.objects.filter(company=request.user.company)\
        .select_related('policy_holder', 'company')
    return Response(ClaimRequestSerializer(claims, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createClaimRequest(request):
    data = request.data.copy()
    if not request.user.is_superuser:
        data['company'] = request.user.company.id  # Automatically assign company for non-superusers
    serializer = ClaimRequestSerializer(data=data)
    return handle_serializer(serializer, success_status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def claimDetails(request, id):
    if request.user.is_superuser:
        claim = get_object_or_404(ClaimRequest, id=id)
    else:
        claim = get_object_or_404(
        ClaimRequest.objects.filter(company=request.user.company), 
        id=id
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateClaim(request, id):
    claim = get_object_or_404(ClaimRequest, id=id)
    
    image_fields = ['bill', 'policy_copy', 'health_report']
    for field in image_fields:
        claim = handle_image_update(claim, field, request.data)
    
    serializer = ClaimRequestSerializer(claim, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteClaim(request, id):
    claim = get_object_or_404(ClaimRequest, id=id)
    claim.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@permission_classes([IsAuthenticated])
def claimsByPolicyHolder(request, policyHolderId):
    claims = ClaimRequest.objects.filter(policy_holder_id=policyHolderId)
    return Response(ClaimRequestSerializer(claims, many=True).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@permission_classes([IsAuthenticated])
def claimsByStatus(request, status):
    claims = ClaimRequest.objects.filter(status=status)
    return Response(ClaimRequestSerializer(claims, many=True).data)

@api_view(['GET'])


# Sales Agent Views


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllAgents(request):
    agents = SalesAgent.objects.all()
    return Response(SalesAgentSerializer(agents, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createAgent(request):
    data = request.data.copy()
    if not request.user.is_superuser:
        data['company'] = request.user.company.id  # Automatically assign company for non-superusers
    serializer = SalesAgentSerializer(data=data)
    return handle_serializer(serializer, success_status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agentDetails(request, id):
    if request.user.is_superuser:
        agent = get_object_or_404(SalesAgent, id=id)
    else:
        agent = get_object_or_404(
        SalesAgent.objects.filter(company=request.user.company), 
        id=id
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateAgent(request, id):
    agent = get_object_or_404(SalesAgent, id=id)
    serializer = SalesAgentSerializer(agent, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteAgent(request, id):
    agent = get_object_or_404(SalesAgent, id=id)
    agent.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def salesAgentsWithPolicies(request):
    agents = SalesAgent.objects.all()
    data = [{
        "id": agent.id,
        "firstName": agent.first_name,
        "lastName": agent.last_name,
        "totalPoliciesSold": agent.total_policies_sold,
    } for agent in agents]
    return Response(data)

# Premium Payment Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllPayments(request):
    payments = PremiumPayment.objects.all()
    return Response(PremiumPaymentSerializer(payments, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createPremiumPayment(request):
    data = request.data.copy()
    if not request.user.is_superuser:
        data['company'] = request.user.company.id  # Automatically assign company for non-superusers
    serializer = PremiumPaymentSerializer(data=data)
    return handle_serializer(serializer, success_status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def paymentDetails(request, id):
    if request.user.is_superuser:
        payment = get_object_or_404(PremiumPayment, id=id)
    else:
        payment = get_object_or_404(
        PremiumPayment.objects.filter(company=request.user.company), 
        id=id
    )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updatePayment(request, id):
    payment = get_object_or_404(PremiumPayment, id=id)
    serializer = PremiumPaymentSerializer(payment, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deletePayment(request, id):
    payment = get_object_or_404(PremiumPayment, id=id)
    payment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def premiumPaymentsDue(request, dueDate):
    payments = PremiumPayment.objects.filter(due_date__lte=dueDate, status="Due")
    return Response(PremiumPaymentSerializer(payments, many=True).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def paymentProcessingByStatus(request, status):
    payments = PaymentProcessing.objects.filter(processing_status=status)
    return Response(PaymentProcessingSerializer(payments, many=True).data)

# Underwriting Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllUnderwritings(request):
    underwritings = Underwriting.objects.all()
    return Response(UnderwritingSerializer(underwritings, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createUnderwriting(request):
    data = request.data.copy()
    if not request.user.is_superuser:
        data['company'] = request.user.company.id  # Automatically assign company for non-superusers
    serializer = UnderwritingSerializer(data=data)
    return handle_serializer(serializer, success_status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def underwritingDetails(request, id):

    if request.user.is_superuser:
        # Superuser can access any underwriting
        underwriting = get_object_or_404(Underwriting, id=id)
    else:
        # Filter underwriting by the user's company
        underwriting = get_object_or_404(
            Underwriting.objects.filter(company=request.user.company), 
            id=id
        )
    return Response(UnderwritingSerializer(underwriting).data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateUnderwriting(request, id):
    underwriting = get_object_or_404(Underwriting, id=id)
    serializer = UnderwritingSerializer(underwriting, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteUnderwriting(request, id):
    underwriting = get_object_or_404(Underwriting, id=id)
    underwriting.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def underwritingByStatus(request, status):
    underwritings = Underwriting.objects.filter(status=status)
    return Response(UnderwritingSerializer(underwritings, many=True).data)
# Employee Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllEmployees(request):
    employees = Employee.objects.all()
    return Response(EmployeeSerializer(employees, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createEmployee(request):
    data = request.data.copy()
    if not request.user.is_superuser:
        data['company'] = request.user.company.id  
    serializer = EmployeeSerializer(data=data)
    return handle_serializer(serializer, success_status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employeeDetails(request, id):
    if request.user.is_superuser:
        employee = get_object_or_404(Employee, id=id)
    else:
        employee = get_object_or_404(
        Employee.objects.filter(company=request.user.company), 
        id=id
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateEmployee(request, id):
    employee = get_object_or_404(Employee, id=id)
    serializer = EmployeeSerializer(employee, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteEmployee(request, id):
    employee = get_object_or_404(Employee, id=id)
    employee.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employeesByPosition(request, positionId):
    employees = Employee.objects.filter(position_id=positionId)
    return Response(EmployeeSerializer(employees, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getAllCompanies(request):
    if not request.user.is_superuser:
        return Response(
            {"error": "Not authorized"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    companies = Company.objects.all()
    return Response(CompanySerializer(companies, many=True).data)



# Create a new company
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createCompany(request):
    if not request.user.is_superuser:
        if hasattr(request.user, 'company'):
            return Response(
                {"error": "You already have an associated company."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Automatically set the company user as the logged-in user
        data = request.data.copy()
        data['user'] = request.user.id
    else:
        # Superusers can create companies without restrictions
        data = request.data

    serializer = CompanySerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Get details of a specific company
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def companyDetails(request, id):
    if not request.user.is_superuser and request.user.company.id != id:
        return Response(
            {"error": "Not authorized"}, 
            status=status.HTTP_403_FORBIDDEN
        )
        
    
    if request.user.is_superuser:
        company = get_object_or_404(Company, id=id)
    else:
        company = get_object_or_404(
        Company.objects.filter(id=id, user=request.user ), 
        id=id
    )


    return Response(CompanySerializer(company).data)

# Update company details

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateCompany(request, id):
    if not request.user.is_superuser and request.user.company.id != id:
        return Response(
            {"error": "Not authorized"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    company = get_object_or_404(Company, id=id)
    serializer = CompanySerializer(company, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Delete a company
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteCompany(request, id):
    if not request.user.is_superuser:
        return Response(
            {"error": "Not authorized"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    company = get_object_or_404(Company, id=id)
    company.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def markPaymentAsPaid(request, payment_id):
    payment = get_object_or_404(PremiumPayment, id=payment_id)
    data = request.data
    amount_paid = Decimal(data.get('amount_paid', 0))

    payment.total_paid += amount_paid
    payment.status = "Paid" if payment.total_paid >= payment.annual_premium else "Partially Paid"
    payment.save()
    return Response(PremiumPaymentSerializer(payment).data)



# html api view
@staff_member_required
def fetch_policyholder_data(request, policy_number):
    print(f"Received policy_number: {policy_number}")  # Debug log
    try:
        policy_holder = PolicyHolder.objects.get(policy_number=policy_number)
        return JsonResponse({
            'sum_assured': float(policy_holder.sum_assured),
            'include_adb': policy_holder.include_adb,
            'include_ptd': policy_holder.include_ptd,
            'payment_interval': policy_holder.payment_interval,
            'policy': {
                'fixed_premium_ratio': float(policy_holder.policy.fixed_premium_ratio),
                'adb_percentage': float(policy_holder.policy.adb_percentage),
                'ptd_percentage': float(policy_holder.policy.ptd_percentage),
                'loading_charges': {
                    interval.interval: float(interval.percentage)
                    for interval in policy_holder.policy.loading_charges.all()
                },
            },
        })
        
    except PolicyHolder.DoesNotExist:
        return JsonResponse({'error': 'Policy holder not found'}, status=404)
def get_policy_holders(request):
    policy_holders = PolicyHolder.objects.all()
    data = [
        {
            "id": holder.id,
            "policy_number": holder.policy_number,
            "name": f"{holder.first_name} {holder.last_name}"
        }
        for holder in policy_holders
    ]
    return JsonResponse(data, safe=False)


def is_superuser(user):
    return user.is_superuser

@login_required
def dashboard_view(request):
    """View for displaying the dashboard based on user permissions."""
    dashboard = Dashboard(request.user)
    
    context = {
        **site.each_context(request),
        'title': 'Dashboard',
        'branch_reports': dashboard.get_branch_reports(),
        'company_report': dashboard.get_company_report(),
        'sales_agent_reports': dashboard.get_sales_agent_reports(),
        'is_branch_view': not request.user.is_superuser,
        'user_branch': getattr(request.user, 'branch', None),
    }
    return render(request, 'dashboard.html', context)

def manage_mortality_rates(request):
    generator_form = MortalityRateGeneratorForm(request.POST or None)
    bulk_form = None
    age_ranges = None

    if request.method == 'POST':
        if 'generate' in request.POST and generator_form.is_valid():
            age_ranges = generator_form.generate_ranges()
            bulk_form = MortalityRateBulkForm(age_ranges=age_ranges)
        
        elif 'save' in request.POST and 'age_ranges' in request.session:
            age_ranges = request.session['age_ranges']
            bulk_form = MortalityRateBulkForm(request.POST, age_ranges=age_ranges)
            
            if bulk_form.is_valid():
                try:
                    # Clear existing rates if needed
                    MortalityRate.objects.all().delete()
                    
                    # Create new rates
                    for i, range_data in enumerate(age_ranges):
                        rate_value = bulk_form.cleaned_data[f'rate_{i}']
                        MortalityRate.objects.create(
                            age_group_start=range_data['start'],
                            age_group_end=range_data['end'],
                            rate=rate_value
                        )
                    messages.success(request, 'Mortality rates have been updated successfully.')
                    return redirect('admin:index')
                except Exception as e:
                    messages.error(request, f'Error saving rates: {str(e)}')

    if age_ranges:
        request.session['age_ranges'] = age_ranges
    
