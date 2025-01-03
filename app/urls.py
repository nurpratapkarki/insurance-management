# urls.py
from django.urls import path
from . import views
from .views import fetch_policyholder_data, get_policy_holders

urlpatterns = [
    # Home/Dashboard
    path('home', views.insuranceHome, name='insuranceHome'),

    # Insurance Policies
    path('policies', views.getAllPolicies, name='getAllPolicies'),
    path('policies/create', views.createPolicy, name='createPolicy'),
    path('policies/<int:id>', views.policyDetails, name='policyDetails'),
    path('policies/<int:id>/update', views.updatePolicy, name='updatePolicy'),
    path('policies/<int:id>/delete', views.deletePolicy, name='deletePolicy'),

    # Policy Holders
    path('policyholders', views.getAllPolicyHolders, name='getAllPolicyHolders'),
    path('policyholders/create', views.createPolicyHolder, name='createPolicyHolder'),
    path('policyholders/<int:id>', views.policyHolderDetails, name='policyHolderDetails'),
    path('policyholders/<int:id>/update', views.updatePolicyHolder, name='updatePolicyHolder'),
    path('policyholders/<int:id>/delete', views.deletePolicyHolder, name='deletePolicyHolder'),
    path('policyholders/branch/<int:branchId>', views.policyHoldersByBranch, name='policyHoldersByBranch'),

    # Claims
    path('claims', views.getAllClaims, name='getAllClaims'),
    path('claims/create', views.createClaimRequest, name='createClaimRequest'),
    path('claims/<int:id>', views.claimDetails, name='claimDetails'),
    path('claims/<int:id>/update', views.updateClaim, name='updateClaim'),
    path('claims/<int:id>/delete', views.deleteClaim, name='deleteClaim'),
    path('claims/policyholder/<int:policyHolderId>', views.claimsByPolicyHolder, name='claimsByPolicyHolder'),
    path('claims/status/<str:status>', views.claimsByStatus, name='claimsByStatus'),

    # Sales Agents
    path('agents/', views.getAllAgents, name='getAllAgents'),
    path('agents/create', views.createAgent, name='createAgent'),
    path('agents/<int:id>', views.agentDetails, name='agentDetails'),
    path('agents/<int:id>/update', views.updateAgent, name='updateAgent'),
    path('agents/<int:id>/delete', views.deleteAgent, name='deleteAgent'),
    path('agents/policies', views.salesAgentsWithPolicies, name='salesAgentsWithPolicies'),

    # Employees
    path('employees', views.getAllEmployees, name='getAllEmployees'),
    path('employees/create', views.createEmployee, name='createEmployee'),
    path('employees/<int:id>', views.employeeDetails, name='employeeDetails'),
    path('employees/<int:id>/update', views.updateEmployee, name='updateEmployee'),
    path('employees/<int:id>/delete', views.deleteEmployee, name='deleteEmployee'),
    path('employees/position/<int:positionId>', views.employeesByPosition, name='employeesByPosition'),

    # Premium Payments
    path('payments', views.getAllPayments, name='getAllPayments'),
    path('payments/create', views.createPremiumPayment, name='createPremiumPayment'),
    path('payments/<int:id>', views.paymentDetails, name='paymentDetails'),
    path('payments/<int:id>/update', views.updatePayment, name='updatePayment'),
    path('payments/<int:id>/delete', views.deletePayment, name='deletePayment'),
    path('payments/due/<str:dueDate>', views.premiumPaymentsDue, name='premiumPaymentsDue'),
    path('payments/status/<str:status>', views.paymentProcessingByStatus, name='paymentProcessingByStatus'),
    path('payments/<int:payment_id>/pay', views.markPaymentAsPaid, name='markPaymentAsPaid'),


    # Underwriting
    path('underwritings', views.getAllUnderwritings, name='getAllUnderwritings'),
    path('underwritings/create', views.createUnderwriting, name='createUnderwriting'),
    path('underwritings/<int:id>', views.underwritingDetails, name='underwritingDetails'),
    path('underwritings/<int:id>/update', views.updateUnderwriting, name='updateUnderwriting'),
    path('underwritings/<int:id>/delete', views.deleteUnderwriting, name='deleteUnderwriting'),
    path('underwritings/status/<str:status>', views.underwritingByStatus, name='underwritingByStatus'),
    # Companies
    path('companies', views.getAllCompanies, name='getAllCompanies'),
    path('companies/create', views.createCompany, name='createCompany'),
    path('companies/<int:id>', views.companyDetails, name='companyDetails'),
    path('companies/<int:id>/update', views.updateCompany, name='updateCompany'),
    path('companies/<int:id>/delete', views.deleteCompany, name='deleteCompany'),
    path('policyholder-data/<int:policy_number>/', views.fetch_policyholder_data, name='fetch_policyholder_data'),
    path('holder/', views.get_policy_holders, name='get_policy_holders'),

]