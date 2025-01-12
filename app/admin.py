from django.contrib import admin
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django import forms

from .models import (
    InsurancePolicy, SalesAgent, PolicyHolder, Underwriting,
    ClaimRequest, ClaimProcessing, PremiumPayment,MortalityRate,
    EmployeePosition, Employee, PaymentProcessing, Branch, Company, AgentReport, AgentApplication, Occupation
)


# Mixin for filtering 'company' and 'user' fields
class CompanyFilterMixin:
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Dynamically filter foreign key fields to show only data relevant to the user's company.
        """
        if not request.user.is_superuser:
            # Filter by company for fields that reference a company
            if db_field.name == "company":
                kwargs["queryset"] = db_field.related_model.objects.filter(id=request.user.company.id)
            elif db_field.name == "user":
                kwargs["queryset"] = db_field.related_model.objects.filter(id=request.user.id)
            else:
                # Filter relational fields dynamically if they have a 'company' field
                try:
                    related_model = db_field.related_model
                    if hasattr(related_model, 'company'):
                        kwargs["queryset"] = related_model.objects.filter(company=request.user.company)
                except AttributeError:
                    pass  # If no related model or company field exists, do nothing

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
# Register the Company
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_code', 'name', 'user', 'email', 'is_active', 'phone_number')
    search_fields = ('name', 'address')
    ordering = ('-id',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)  # Company is directly tied to the user
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user" and not request.user.is_superuser:
            # Restrict to only the logged-in user for non-superusers
            kwargs["queryset"] = User.objects.filter(id=request.user.id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
#Register occupation

@admin.register(Occupation)
class OccupationAdmin(admin.ModelAdmin):
    list_display = ('name', 'risk_category')
    list_filter = ('risk_category',)
    search_fields = ('name',)
# Register Insurance Policy
@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'min_sum_assured', 'max_sum_assured', 'quarterly_loading', 'semi_annual_loading')
    search_fields = ('name', 'company__name')
    list_filter = ('company',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)

class AgentReportInline(admin.TabularInline):
    model = AgentReport
    extra = 0
    can_delete = False
    readonly_fields = ('report_date', 'policies_sold', 'total_premium', 'commission_earned', 'target_achievement')
    verbose_name = "Agent Report"
    verbose_name_plural = "Agent Reports"
# Register Sales Agent
@admin.register(SalesAgent)
class SalesAgentAdmin(CompanyFilterMixin,admin.ModelAdmin):
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
        

@admin.register(PolicyHolder)
class PolicyHolderAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'status', 'policy', 'sum_assured', 'payment_interval', 'occupation')
    search_fields = ('first_name', 'last_name', 'policy__name')
    list_filter = ('status', 'policy', 'occupation')

    # Fieldsets for organizing data
    fieldsets = (
        ("Personal Information", {
            'fields': (
                'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth', 
                'phone_number',  'emergency_contact_name', 
                'emergency_contact_number', 'occupation', 'yearly_income','status'
            )
        }),
        ("Document Details", {
            'fields': (
                'document_type', 'document_number', 'document_front', 'document_back', 
                'pp_photo', 'pan_Number', 'pan_front', 'pan_back', 'assets_details'
            )
        }),
        ("Address & Geographic Details", {
            'fields': (
                'provience', 'district', 'municipality', 'ward', 'nearest_hospital', 'natural_hazard_exposure'
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
                'heath_history', 'habits', 'dietary_habits', 'work_environment_risk','alcholic', 'smoker','past_medical_report','recent_medical_reports'
            )
        }),
    )

    # Inline editing for related models if necessary
    inlines = []  # Include related inlines if required.


def save_model(self, request, obj, form, change):
    # Save the PolicyHolder instance first
    super().save_model(request, obj, form, change)

    # Perform related operations after the PolicyHolder instance is saved
    if obj.status == "approved":  # Assuming "approved" triggers underwriting
        # Create or update underwriting
        underwriting, created = Underwriting.objects.get_or_create(policy_holder=obj)

        # Update premium payments
        PremiumPayment.objects.filter(policy_holder=obj).delete()  # Clear existing payments
        premium_payment = PremiumPayment(policy_holder=obj)
        premium_payment.save()  # Automatically triggers the premium calculation logic

        super().save_model(request, obj, form, change)
    def get_queryset(self, request):
        """
        Filter queryset based on the user's company if not a superuser.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)

    
# Register Underwriting
@admin.register(Underwriting)
class UnderwritingAdmin(admin.ModelAdmin):
    list_display = ('policy_holder', 'risk_assessment_score', 'risk_category', 'remarks')
    readonly_fields = ('risk_assessment_score', 'risk_category')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)
    

# Register Claim Request
@admin.register(ClaimRequest)
class ClaimRequestAdmin(CompanyFilterMixin , admin.ModelAdmin):
    list_display = ('id', 'policy_holder', 'claim_date', 'status')
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name')
    list_filter = ('status', 'claim_date')
    ordering = ('-claim_date',)
    list_per_page = 25

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)


# Register Claim Processing
@admin.register(ClaimProcessing)
class ClaimProcessingAdmin(admin.ModelAdmin):
    list_display = ('id', 'claim_request', 'processing_status', 'processing_date')
    list_filter = ('processing_status', 'processing_date')
    search_fields = ('claim_request__policy_holder__first_name', 'claim_request__policy_holder__last_name')
    ordering = ('-processing_date',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)

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

# Register Premium Payment
@admin.register(PremiumPayment)
class PremiumPaymentAdmin(admin.ModelAdmin):
    list_display = ('policy_holder', 'annual_premium', 'interval_payment', 'total_paid')
    readonly_fields = ('annual_premium', 'interval_payment')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj and 'policy_holder' in request.GET:
            policy_holder_id = request.GET.get('policy_holder')
            try:
                policy_holder = PolicyHolder.objects.get(id=policy_holder_id)
                payment = PremiumPayment(policy_holder=policy_holder)
                annual_premium, interval_payment = payment.calculate_premium()
                form.base_fields['annual_premium'].initial = annual_premium
                form.base_fields['interval_payment'].initial = interval_payment
            except PolicyHolder.DoesNotExist:
                pass
        return form
    def save_model(self, request, obj, form, change):
        obj.amount = obj.calculate_premium()
        super().save_model(request, obj, form, change)

    def add_payment(self, request, queryset):
        """
        Custom admin action to update payment status and total paid.
        """
        for payment in queryset:
            payment.total_paid += payment.amount  # Increment total_paid by interval amount

            # Update payment status
            if payment.total_paid >= payment.annual_premium:
                payment.status = "Paid"
            else:
                payment.status = "Partially Paid"

            payment.save()

        # Notify admin
        self.message_user(request, "Payments updated successfully.", level="success")
    add_payment.short_description = "Mark selected payments as received"




            


# Register Employee Position
@admin.register(EmployeePosition)
class EmployeePositionAdmin(admin.ModelAdmin):
    list_display = ('id', 'position')
    search_fields = ('position',)
    ordering = ('position',)


# Register Employee
@admin.register(Employee)
class EmployeeAdmin(CompanyFilterMixin,admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'gender', 'date_of_birth', 'employee_position')
    list_filter = ('gender', 'employee_position')
    search_fields = ('name', 'address')
    ordering = ('-date_of_birth',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)


# Register Payment Processing
@admin.register(PaymentProcessing)
class PaymentProcessingAdmin( CompanyFilterMixin,admin.ModelAdmin):
    list_display = ('id', 'name', 'processing_status', 'claim_request', 'date_of_processing')
    list_filter = ('processing_status', 'date_of_processing')
    search_fields = ('name', 'claim_request__policy_holder__first_name', 'claim_request__policy_holder__last_name')
    ordering = ('-date_of_processing',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)


# Register Branch
@admin.register(Branch)
class BranchAdmin(CompanyFilterMixin ,admin.ModelAdmin):
    list_display = ('branch_code', 'name', 'location')
    search_fields = ('name',)
    ordering = ('-id',)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)
    
    # agent application
@admin.register(AgentApplication)
class AgentApplicationAdmin(CompanyFilterMixin,admin.ModelAdmin):
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
