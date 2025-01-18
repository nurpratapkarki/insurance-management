from django.contrib import admin
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import date
from django.core.exceptions import ValidationError
from django import forms
from django.db.models import Sum
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    InsurancePolicy, SalesAgent, PolicyHolder, Underwriting,
    ClaimRequest, ClaimProcessing, PremiumPayment,MortalityRate,
    EmployeePosition, Employee, PaymentProcessing, Branch, Company, AgentReport, AgentApplication, Occupation, DurationFactor, GSVRate, SSVConfig, Bonus, BonusRate, Loan, LoanRepayment,UserProfile
)


# Mixin for filtering 'Branch' and 'user' fields
class BranchFilterMixin:
    def get_queryset(self, request):
        """Filter queryset based on the user's branch and company."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # Superusers see all data

        # Restrict access to branch-specific data
        if hasattr(self.model, 'branch'):
            return qs.filter(branch=request.user.profile.branch)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
        # Handle branch filtering
            if db_field.name == "branch":
                branch = getattr(request.user.profile, "branch", None)
            if branch and branch.pk is not None:  # Check if branch is saved
                kwargs["queryset"] = Branch.objects.filter(id=branch.id)
            else:
                kwargs["queryset"] = Branch.objects.none()  # Provide an empty queryset for unsaved instances

        # Handle company filtering
        elif db_field.name == "company":
            company = getattr(request.user.profile, "company", None)
            if company and company.pk is not None:  # Check if company is saved
                kwargs["queryset"] = Company.objects.filter(id=company.id)
            else:
                kwargs["queryset"] = Company.objects.none()  # Provide an empty queryset for unsaved instances

        return super().formfield_for_foreignkey(db_field, request, **kwargs)




#Register occupation

@admin.register(Occupation)
class OccupationAdmin(admin.ModelAdmin):
    list_display = ('name', 'risk_category')
    list_filter = ('risk_category',)
    search_fields = ('name',)

class GSVRateInline(admin.TabularInline):
    model = GSVRate
    extra = 0

class SSVConfigInline(admin.TabularInline):
    model = SSVConfig
    extra = 0

    
# Register Insurance Policy
@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_sum_assured', 'max_sum_assured')
    search_fields = ('name', 'policy_type')
    inlines = [GSVRateInline, SSVConfigInline]

    def save_model(self, request, obj, form, change):
        if obj.policy_type == "Term" and obj.base_multiplier != 1.0:
            messages.error(request, "Base multiplier for Term insurance must be 1.0.")
            return  # Skip saving

        # Save the policy to ensure it has a primary key
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        """
        Override save_related to ensure the policy is saved 
        before saving related objects (GSVRate, SSVConfig).
        """
        # Save the main object (InsurancePolicy)
        if not form.instance.pk:
            form.instance.save()
        super().save_related(request, form, formsets, change)

    def response_add(self, request, obj, post_url_continue=None):
        """
        Customize the response to guide the user after adding the policy.
        """
        if "_continue" in request.POST:
            messages.info(
                request, 
                "Insurance Policy saved! You can now add GSV and SSV rates."
            )
        return super().response_add(request, obj, post_url_continue)

#Bonus Rate Admin
@admin.register(BonusRate)
class BonusRateAdmin(admin.ModelAdmin):
    list_display = ('year', 'bonus_rate')
    ordering = ['-year']
    search_fields = ('year',)

#Bonus admin
@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):
    list_display = ('policy_holder', 'bonus_type', 'accrued_amount', 'start_date', 'last_updated')
    list_filter = ('bonus_type',)
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name')


class AgentReportInline(admin.TabularInline):
    model = AgentReport
    extra = 0
    can_delete = False
    readonly_fields = ('report_date', 'policies_sold', 'total_premium', 'commission_earned', 'target_achievement')
    verbose_name = "Agent Report"
    verbose_name_plural = "Agent Reports"
# Register Sales Agent
@admin.register(SalesAgent)
class SalesAgentAdmin(BranchFilterMixin,admin.ModelAdmin):
    list_display = ('id', 'agent_code', 'get_application_name', 'is_active', 'commission_rate', 'joining_date')
    search_fields = ('agent_code', 'application__first_name', 'application__last_name')
    list_filter = ('is_active',)
    ordering = ('-joining_date',)
    inlines = [AgentReportInline]
    

    def get_application_name(self, obj):
        if obj.application:
            return f"{obj.application.first_name} {obj.application.last_name}"
        return "N/A"
    get_application_name.short_description = 'Agent Name'

    def save_model(self, request, obj, form, change):
        # Populate non-document fields from the related AgentApplication
        if obj.application:
            obj.agent_code = f"A-{obj.company.id}-{obj.branch.id}-{str(obj.application.id).zfill(4)}"
        super().save_model(request, obj, form, change)
        
#Bonus inline for the policyholder
class BonusInline(admin.TabularInline):
    model = Bonus
    extra = 0
    readonly_fields = ('bonus_type', 'accrued_amount', 'start_date', 'last_updated', 'total_bonus_accrued')

    def total_bonus_accrued(self, obj):
        """Calculate the total bonus accrued for the policyholder."""
        if obj:
            total = Bonus.objects.filter(policy_holder=obj.policy_holder).aggregate(total=Sum('accrued_amount'))['total']
            return total or Decimal('0.00')
        return Decimal('0.00')

    total_bonus_accrued.short_description = 'Total Bonus Accrued'  # Label for the column
@admin.register(PolicyHolder)
class PolicyHolderAdmin(admin.ModelAdmin, BranchFilterMixin):
    list_display = ('first_name', 'last_name', 'status', 'policy', 'sum_assured', 
                   'payment_interval', 'occupation', 'maturity_date')
    search_fields = ('first_name', 'last_name', 'policy__name')
    list_filter = ('status', 'policy', 'occupation')
    inlines = [BonusInline]
    fieldsets = (
        ("Personal Information", {
            'fields': (
                'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth',
                'phone_number', 'emergency_contact_name', 'emergency_contact_number', 
                'occupation', 'yearly_income', 'status', 'start_date'
            )
        }),
        ("Document Details", {
            'fields': (
                'document_type', 'document_number', 'document_front', 'document_back',
                'pp_photo', 'pan_number', 'pan_front', 'pan_back', 'assets_details'
            )
        }),
        ("Address & Geographic Details", {
            'fields': (
                'province', 'district', 'municipality', 'ward', 'nearest_hospital', 
                'natural_hazard_exposure'
            )
        }),
        ("Policy Details", {
            'fields': (
                'company', 'branch', 'policy', 'policy_number', 'agent',
                'sum_assured', 'duration_years', 'payment_interval', 'payment_status',
                'include_adb', 'include_ptd'
            )
        }),
        ("Nominee Details", {
            'fields': (
                'nominee_name', 'nominee_relation', 'nominee_document_type',
                'nominee_document_number', 'nominee_document_front',
                'nominee_document_back', 'nominee_pp_photo'
            )
        }),
        ("Habits & Health Details", {
            'fields': (
                'health_history', 'habits', 'dietary_habits', 'work_environment_risk',
                'alcoholic', 'smoker', 'past_medical_report', 'recent_medical_reports'
            )
        }),
    )

    def get_queryset(self, request):
        """Filter queryset based on user's company access"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(branch=request.user.profile.branch)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter foreign key choices based on user's company"""
        if db_field.name == "policy" and not request.user.is_superuser:
            kwargs["queryset"] = InsurancePolicy.objects.filter(
                company=request.user.company
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """Handle PolicyHolder save"""
        try:
            # Set company from user if not set
            if not obj.company and not request.user.is_superuser:
                obj.company = request.user.company

            # Validate required fields for new policy holders
            if not change:
                if not obj.sum_assured:
                    form.add_error('sum_assured', 'Sum assured is required.')
                    return
                if not obj.policy:
                    form.add_error('policy', 'Insurance policy is required.')
                    return

            # Save the object - validation will happen in model's save method
            obj.save()

        except ValidationError as e:
            form._errors.update(e.message_dict)
            messages.error(request, "Validation error occurred while saving the PolicyHolder.")

             
# Register Underwriting
@admin.register(Underwriting)
class UnderwritingAdmin(admin.ModelAdmin, BranchFilterMixin):
    list_display = ('policy_holder', 'risk_assessment_score', 'risk_category', 'remarks')
    readonly_fields = ('risk_assessment_score', 'risk_category')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch=request.user.profile.branch)
    

# Register Claim Request
@admin.register(ClaimRequest)
class ClaimRequestAdmin(admin.ModelAdmin, BranchFilterMixin):
    list_display = ('policy_holder', 'claim_date', 'status', 'claim_amount')
    readonly_fields = ('claim_amount',)
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name')


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch=request.user.profile.branch)


# Register Claim Processing
@admin.register(ClaimProcessing)
class ClaimProcessingAdmin(admin.ModelAdmin, BranchFilterMixin):
    list_display = ('claim_request', 'processing_status', 'processing_date')
    search_fields = ('claim_request__policy_holder__first_name', 'claim_request__policy_holder__last_name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch=request.user.profile.branch)

#Forms for the Premium Payment
class PremiumPaymentForm(forms.ModelForm):
    class Meta:
        model = PremiumPayment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'policy_holder' in self.fields:
            self.fields['policy_holder'].queryset = PolicyHolder.objects.all()
            self.fields['policy_holder'].label_from_instance = (
                lambda obj: f"{obj.policy_number} - {obj.first_name} {obj.last_name}"
            )
            self.fields['policy_holder'].to_field_name = 'policy_number'  # Use policy_number as the value


# Register Duration Factor
@admin.register(DurationFactor)
class DurationFactorAdmin(admin.ModelAdmin):
    list_display = ( 'policy_type', 'min_duration', 'max_duration', 'factor')
    list_filter = ( 'policy_type', 'factor')
    search_fields = ('company__name',)

    
# Register Premium Payment

@admin.register(PremiumPayment)
class PremiumPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'policy_holder', 'annual_premium', 'total_premium', 'interval_payment',
        'total_paid', 'payment_status', 'next_payment_date'
    )
    list_filter = ('payment_status', 'policy_holder__payment_interval')
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name', 'policy_holder__policy_number')
    readonly_fields = (
        'annual_premium', 'interval_payment', 'total_premium',
        'remaining_premium','total_paid' , 'gsv_value', 'ssv_value'
    )
    
    actions = ['add_payment']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(policy_holder__branch=request.user.profile.branch)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        """Initialize form with calculated premium values"""
        form = super().get_form(request, obj, **kwargs)
        if not obj and 'policy_holder' in request.GET:
            try:
                policy_holder = PolicyHolder.objects.get(
                    id=request.GET.get('policy_holder')
                )
                payment = PremiumPayment(policy_holder=policy_holder)
                annual_premium, interval_payment = payment.calculate_premium()
                form.base_fields['annual_premium'].initial = annual_premium
                form.base_fields['interval_payment'].initial = interval_payment
            except PolicyHolder.DoesNotExist:
                pass
        return form

    def add_payment(self, request, queryset):
        """Admin action to record payments"""
        for payment in queryset:
            payment.add_payment(payment.interval_payment)
        self.message_user(request, "Payments recorded successfully")
    add_payment.short_description = "Record payment for selected items"

    def save_model(self, request, obj, form, change):
        try:
            if obj.paid_amount < 0:
                raise ValidationError("Paid amount cannot be negative")
                
            super().save_model(request, obj, form, change)
            
            if obj.paid_amount > 0:
                self.message_user(
                    request,
                    f"Payment of {obj.paid_amount} recorded successfully. Total paid: {obj.total_paid}",
                    messages.SUCCESS
                )
        except ValidationError as e:
            self.message_user(request, str(e), messages.ERROR)


            


# Register Employee Position
@admin.register(EmployeePosition)
class EmployeePositionAdmin(admin.ModelAdmin):
    list_display = ('id', 'position')
    search_fields = ('position',)
    ordering = ('position',)


# Register Employee
@admin.register(Employee)
class EmployeeAdmin(BranchFilterMixin,admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'gender', 'date_of_birth', 'employee_position')
    list_filter = ('gender', 'employee_position')
    search_fields = ('name', 'address')
    ordering = ('-date_of_birth',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch=request.user.profile.branch)


# Register Payment Processing
@admin.register(PaymentProcessing)
class PaymentProcessingAdmin(admin.ModelAdmin, BranchFilterMixin):
    list_display = ('name', 'processing_status', 'date_of_processing')
    search_fields = ('name', 'claim_request__policy_holder__first_name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(branch=request.user.profile.branch)
    
#Branch admin registration

# agent application
@admin.register(AgentApplication)
class AgentApplicationAdmin(BranchFilterMixin,admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'company', 'branch',
        'email', 'phone_number', 'status', 'created_at'
    )
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')
    list_filter = ('company', 'branch', 'status', 'gender', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        ("Personal Information", {
            'fields': (
                'first_name', 'last_name', 'father_name', 'mother_name',
                'grand_father_name', 'grand_mother_name', 'gender',
                'date_of_birth', 'email', 'phone_number', 'address'
            )
        }),
        ("Document Details", {
            'fields': (
                'resume', 'citizenship_front', 'citizenship_back',
                'license_front', 'license_back', 'pp_photo',
                'license_number', 'license_issue_date', 'license_expiry_date',
                'license_type', 'license_issue_district', 'license_issue_zone',
                'license_issue_province', 'license_issue_country'
            )
        }),
        ("Company and Branch Information", {
            'fields': ('company', 'branch')
        }),
        ("Status Information", {
            'fields': ('status', 'created_at')
        }),
    )

@admin.register(MortalityRate)
class MortalityRateAdmin(admin.ModelAdmin):
    list_display = ('company', 'age_group_start', 'age_group_end', 'rate')
    list_filter = ('company',)
    search_fields = ('company__name',)


#Loan Admin
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin, BranchFilterMixin):
    list_display = ('policy_holder', 'loan_amount', 'remaining_balance', 'accrued_interest', 'loan_status', 'created_at')
    readonly_fields = ('remaining_balance', 'accrued_interest', 'last_interest_date')
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name')
#Loan Repayment Admin
@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin, BranchFilterMixin):
    list_display = ('loan', 'amount', 'repayment_type', 'repayment_date', 'remaining_loan_balance')
    readonly_fields = ('remaining_loan_balance',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_code', 'email', 'is_active')
    search_fields = ('name', 'company_code')
    list_filter = ('is_active',)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch_code', 'company', 'location')
    search_fields = ('name', 'branch_code')
    list_filter = ('company',)
    readonly_fields = ('company',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(company=request.user.profile.company)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "company" and not request.user.is_superuser:
            kwargs["queryset"] = Company.objects.filter(id=request.user.profile.company.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'company')
    search_fields = ('user__username', 'branch__name', 'company__name')
    list_filter = ('company', 'branch')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(company=request.user.profile.company)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(company=request.user.profile.company)
            elif db_field.name == "company":
                kwargs["queryset"] = Company.objects.filter(id=request.user.profile.company.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Unregister the default User admin and register custom one
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_superuser', 'get_branch', 'get_company')
    search_fields = ('username', 'email')
    list_filter = ('is_superuser', 'is_active')

    def get_branch(self, obj):
        return obj.profile.branch.name if obj.profile.branch else "Not Assigned"
    
    def get_company(self, obj):
        return obj.profile.company.name if obj.profile.company else "Not Assigned"
    
    get_branch.short_description = 'Branch'
    get_company.short_description = 'Company'

    def save_model(self, request, obj, form, change):
        creating = not obj.pk
        super().save_model(request, obj, form, change)
        
        if creating and not obj.is_superuser:
            # For new non-superuser, try to assign first company
            first_company = Company.objects.first()
            if first_company:
                obj.profile.company = first_company
                obj.profile.save()
    