from django.contrib import admin
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.contrib import messages
from django.core.exceptions import ValidationError
from django import forms

from .models import (
    InsurancePolicy, SalesAgent, PolicyHolder, Underwriting,
    ClaimRequest, ClaimProcessing, PremiumPayment,
    EmployeePosition, Employee, PaymentProcessing, Branch, Company, LoadingCharge, AgentReport, AgentApplication
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


class LoadingChargeInline(admin.StackedInline):
    model = LoadingCharge
    extra = 1  # Number of empty forms to display
    can_delete = True  # Allow deletion of inline items
    verbose_name = "Loading Charge"
    verbose_name_plural = "Loading Charges"
# Register Insurance Policy
@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(CompanyFilterMixin,admin.ModelAdmin):
    list_display = ('id', 'name', 'policy_type', 'created_at')
    search_fields = ('name',)
    list_filter = ('policy_type',)
    inlines = [LoadingChargeInline]
    ordering = ('-id',)

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
        

@receiver(post_save, sender=AgentApplication)
def create_sales_agent(sender, instance, **kwargs):
    if instance.status == "Approved" and not hasattr(instance, 'sales_agent'):
        # Automatically create a SalesAgent
        SalesAgent.objects.create(
            company=instance.company,
            branch=instance.branch,
            application=instance,
            agent_code=f"A-{instance.company.id}-{instance.branch.id}-{str(instance.id).zfill(4)}",
            commission_rate=5.00  # Default commission rate
        )

@admin.register(PolicyHolder)
class PolicyHolderAdmin(admin.ModelAdmin):
    list_display = ('policy_number', 'first_name', 'last_name', 'policy', 'payment_status', 'phone_number')
    search_fields = ('first_name', 'last_name', 'policy_number', 'phone_number')
    list_filter = ('gender', 'policy', 'payment_status', 'branch', 'company')
    ordering = ('-id',)

    # Organize fields into tabs using fieldsets
    fieldsets = (
        ("Personal Information", {
            'fields': (
                'first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth', 
                'phone_number'
            )
        }),
        ("Policy Details", {
            'fields': (
                'company', 'branch', 'policy', 'policy_number', 'agent',
                'sum_assured', 'payment_interval', 'payment_status','include_adb', 'include_ptd','duration_years'
            )
        }),
        ("Document Details", {
            'fields': (
                'document_type', 'document_number', 'document_front', 'document_back', 'pp_photo'
            )
        }),
        ("Nominee Details", {
            'fields': (
                'nominee_name', 'nominee_relation', 'nominee_document_type', 
                'nominee_document_number', 'nominee_document_front', 
                'nominee_document_back', 'nominee_pp_photo'
            )
        }),
        ("Address Details", {
            'fields': (
                'provience', 'district', 'municipality', 'ward'
            )
        }),
        
    )

    def get_queryset(self, request):
        """
        Filter queryset based on the user's company if not a superuser.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)

    def save_model(self, request, obj, form, change):
    
        try:
            if obj.policy:
                if obj.sum_assured < obj.policy.min_sum_assured or obj.sum_assured > obj.policy.max_sum_assured:
                    raise ValidationError(
                    f"Sum assured must be between {obj.policy.min_sum_assured} and {obj.policy.max_sum_assured}."
                )
            super().save_model(request, obj, form, change)
        except ValidationError as e:
        # Add error message to Django Admin
            form.add_error(None, e)
            messages.error(request, f"Error: {e}")
# Register Underwriting
@admin.register(Underwriting)
class UnderwritingAdmin(CompanyFilterMixin ,admin.ModelAdmin):
    list_display = ('id', 'policy_holder', 'policy', 'status', 'risk_assessment_score', 'evaluated_by', 'evaluation_date')
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name', 'status')
    list_filter = ('status', 'evaluation_date')
    ordering = ('-evaluation_date',)

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
class PremiumPaymentAdmin(CompanyFilterMixin, admin.ModelAdmin):
    list_display = ('id', 'policy_holder', 'annual_premium', 'amount', 'payment_date', 'status')
    list_filter = ('status', 'payment_date', 'due_date', 'company')
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name', 'status')
    ordering = ('-payment_date',)
    class Media:
        js = ('js/premium_payment_admin.js',)
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Prepopulate premium values for new entries
        if not obj and 'policy_holder' in request.GET:
            policy_holder_id = request.GET.get('policy_holder')
            try:
                policy_holder = PolicyHolder.objects.get(id=policy_holder_id)
                premium_payment = PremiumPayment(policy_holder=policy_holder)
                _, loaded_annual_premium, interval_payment = premium_payment.calculate_premium()

                form.base_fields['annual_premium'].initial = loaded_annual_premium
                form.base_fields['amount'].initial = interval_payment
            except PolicyHolder.DoesNotExist:
                pass

        return form

    def save_model(self, request, obj, form, change):
        # Calculate premiums before saving
        if not obj.annual_premium or not obj.amount:
            _, obj.annual_premium, obj.amount = obj.calculate_premium()
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

# Signal to update PremiumPayment when PolicyHolder changes
@receiver(post_save, sender=PolicyHolder)
def update_premium_payments_on_policyholder_change(sender, instance, **kwargs):
    premium_payments = PremiumPayment.objects.filter(policy_holder=instance)
    for payment in premium_payments:
        _, loaded_annual_premium, interval_payment = payment.calculate_premium()
        payment.annual_premium = loaded_annual_premium
        payment.amount = interval_payment
        payment.save()

@receiver(post_save, sender=InsurancePolicy)
def update_premium_payments_on_policy_change(sender, instance, **kwargs):
    policy_holders = instance.policy_holders.all()
    for policy_holder in policy_holders:
        premium_payments = PremiumPayment.objects.filter(policy_holder=policy_holder)
        for payment in premium_payments:
            _, loaded_annual_premium, interval_payment = payment.calculate_premium()
            payment.annual_premium = loaded_annual_premium
            payment.amount = interval_payment
            payment.save()



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