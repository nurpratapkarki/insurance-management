from django.contrib import admin
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import date
from django.core.exceptions import ValidationError
from django import forms
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import path
from decimal import Decimal
from django.db.models import Sum
from .views import manage_mortality_rates  
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .frontend_data import *
from .models import (
    InsurancePolicy, SalesAgent, PolicyHolder, Underwriting,
    ClaimRequest, ClaimProcessing, PremiumPayment,MortalityRate,
    EmployeePosition, Employee, PaymentProcessing, Branch, Company, AgentReport, AgentApplication, Occupation, DurationFactor, GSVRate, SSVConfig, Bonus, BonusRate, Loan, LoanRepayment,UserProfile
)


# Mixin for filtering 'Branch' and 'user' fields
class BranchFilterMixin:
    def get_queryset(self, request):
        """Filter queryset based on the user's branch."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(self.model, 'branch'):
            return qs.filter(branch=request.user.profile.branch)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter branch-related fields for non-superusers."""
        if db_field.name == "branch" and not request.user.is_superuser:
            branch = getattr(request.user.profile, "branch", None)
            kwargs["queryset"] = Branch.objects.filter(id=branch.id) if branch else Branch.objects.none()
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
    list_display = ('year', 'policy_type', 'min_year', 'max_year', 'bonus_per_thousand')
    ordering = ['year', 'policy_type', 'min_year']
    search_fields = ('year', 'policy_type')
    list_filter = ('year', 'policy_type')

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
        return f"{obj.application.first_name} {obj.application.last_name}" if obj.application else "N/A"
    
    get_application_name.short_description = 'Agent Name'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            return qs.filter(branch=request.user.profile.branch)
        return qs
    
    def save_model(self, request, obj, form, change):
        # Populate non-document fields from the related AgentApplication
        if obj.application:
            obj.agent_code = f"A-{obj.branch.id}-{str(obj.application.id).zfill(4)}"
        super().save_model(request, obj, form, change)
        
#Bonus inline for the policyholder
class BonusAdmin(admin.ModelAdmin):
    list_display = ('id', 'policyholder', 'bonus_amount', 'bonus_date')
    list_filter = ('bonus_date',)
    search_fields = ('policyholder__first_name', 'policyholder__last_name')
    
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
    
    
class UnderwritingInline(admin.StackedInline):
    model = Underwriting
    extra = 0
    readonly_fields = ( 'risk_category', 'last_updated_by', 'last_updated_at')

    
@admin.register(PolicyHolder)
class PolicyHolderAdmin(BranchFilterMixin, admin.ModelAdmin):
    list_display = ('policy_number','first_name', 'last_name', 'status', 'policy', 'sum_assured', 
                    'payment_interval', 'occupation', 'maturity_date')
    search_fields = ('first_name', 'last_name','policy_number')
    list_filter = ('status', 'policy', 'occupation')
    inlines = [BonusInline, UnderwritingInline]
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
                'branch', 'policy', 'policy_number', 'agent',
                'sum_assured', 'duration_years', 'payment_interval', 'payment_status',
                'include_adb', 'include_ptd','risk_category'
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
        """Limit PolicyHolder queryset to user's branch."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        branch = getattr(request.user.profile, 'branch', None)
        return qs.filter(branch=branch) if branch else qs.none()


def formfield_for_foreignkey(self, db_field, request, **kwargs):
    if not request.user.is_superuser:
        if db_field.name == "policy":
            user_company = getattr(request.user.profile.branch, 'company', None)
            if user_company:
                kwargs["queryset"] = InsurancePolicy.objects.filter(
                    branch__company=user_company
                )
            else:
                kwargs["queryset"] = InsurancePolicy.objects.none()
        elif db_field.name == "branch":
            user_branch = getattr(request.user.profile, 'branch', None)
            if user_branch:
                kwargs["queryset"] = Branch.objects.filter(id=user_branch.id)
            else:
                kwargs["queryset"] = Branch.objects.none()
    return super().formfield_for_foreignkey(db_field, request, **kwargs)


    def save_model(self, request, obj, form, change):
        """Save model with additional validation and branch assignment"""
        try:
            # Set branch if not set
            if not obj.branch and hasattr(request.user, 'profile'):
                obj.branch = request.user.profile.branch

            # Validate required fields
            if not change:  # Only for new policy holders
                if not obj.sum_assured:
                    form.add_error('sum_assured', 'Sum assured is required.')
                    return
                if not obj.policy:
                    form.add_error('policy', 'Insurance policy is required.')
                    return

            obj.save()
            
        except ValidationError as e:
            form._errors.update(e.message_dict)
            messages.error(request, "Validation error occurred while saving the PolicyHolder.")
            
    def has_module_permission(self, request):
        """Check if user has permission to access the module"""
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'profile') and request.user.profile.branch is not None

    def has_add_permission(self, request):
        """Check if user has permission to add policy holders"""
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        """Check if user has permission to change policy holders"""
        if not self.has_module_permission(request):
            return False
        if obj and not request.user.is_superuser:
            return obj.branch == request.user.profile.branch
        return True

    def has_delete_permission(self, request, obj=None):
        """Check if user has permission to delete policy holders"""
        return self.has_change_permission(request, obj)
# Register Underwriting


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
class EmployeeAdmin(BranchFilterMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'gender', 'date_of_birth', 'employee_position')
    list_filter = ('gender', 'employee_position')
    search_fields = ('name', 'address')
    ordering = ('-date_of_birth',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            return qs.filter(branch=request.user.profile.branch)
        return qs


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
    list_display = ('id', 'first_name', 'last_name', 'branch', 'email', 'phone_number', 'status', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')
    list_filter = ('branch', 'status', 'gender', 'created_at')
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
                'license_issue_province', 'license_issue_country', 'branch'
            )
        }),
        
        ("Status Information", {
            'fields': ('status', 'created_at')
        }),
    )
    def save_model(self, request, obj, form, change):
        # Automatically assign branch for non-superusers
        if not change and not request.user.is_superuser:
            obj.branch = getattr(request.user.profile, 'branch', None)
        super().save_model(request, obj, form, change)
        
@admin.register(MortalityRate)
class MortalityRateAdmin(admin.ModelAdmin):
    list_display = ('age_range_display', 'rate', 'edit_button')
    search_fields = ('age_group_start', 'age_group_end')
    change_list_template = "mortalityrate/mortality_changelist.html"
    change_form_template = "mortalityrate/mortality_from.html"
    
    #changelist view
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Get all mortality rates for the chart
        rates = MortalityRate.objects.all().order_by('age_group_start')
        age_ranges = [f"{rate.age_group_start}-{rate.age_group_end}" for rate in rates]
        rate_values = [float(rate.rate) for rate in rates]
        
        extra_context.update({
            'age_ranges': age_ranges,
            'rates': rate_values,
        })
        
        return super().changelist_view(request, extra_context=extra_context)
    # change view
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        
        if obj:
            # Get all mortality rates for the chart
            rates = MortalityRate.objects.all().order_by('age_group_start')
            age_ranges = [f"{rate.age_group_start}-{rate.age_group_end}" for rate in rates]
            rate_values = [float(rate.rate) for rate in rates]
            
            extra_context.update({
                'age_ranges': age_ranges,
                'rates': rate_values,
                'show_chart': True
            })
            
            # For edit view
            ModelForm = self.get_form(request, obj)
            form = ModelForm(instance=obj)
            
            extra_context.update({
                'form': form,
                'original': obj,
                'show_save': True,
                'show_save_and_continue': True,
            })
            
        return super().change_view(request, object_id, form_url, extra_context)
    def age_range_display(self, obj):
        return f"{obj.age_group_start}-{obj.age_group_end}"
    age_range_display.short_description = "Age Range"

    def edit_button(self, obj):
        return format_html(
            '<a class="button btn btn-warning btn-sm" href="{}">Edit</a>',
            reverse('admin:app_mortalityrate_change', args=[obj.pk])
        )
    edit_button.short_description = 'Edit'

    def add_view(self, request, form_url='', extra_context=None):
        ModelForm = self.get_form(request)
        form = ModelForm()
        
        if request.method == 'POST':
            if 'generate' in request.POST:
                generator_form = MortalityRateGeneratorForm(request.POST)
                if generator_form.is_valid():
                    step = generator_form.cleaned_data['step_size']
                    max_age = generator_form.cleaned_data['max_age']
                    
                    age_ranges = []
                    for age in range(0, max_age, step):
                        age_ranges.append({
                            'start': age,
                            'end': min(age + step - 1, max_age),
                            'rate': 0.00
                        })
                    
                    request.session['generated_ranges'] = age_ranges
                    bulk_form = MortalityRateBulkForm(age_ranges=age_ranges)
                    
                    context = {
                        'form': form,
                        'generated_ranges': age_ranges,
                        'bulk_form': bulk_form,
                        'show_generator': True,
                        'generator_form': generator_form,
                        'opts': self.model._meta,
                        'add': True,
                        'is_popup': False,
                        'save_as': False,
                        'has_delete_permission': False,
                        'has_add_permission': True,
                        'has_change_permission': True,
                        'show_save': True,
                        'show_save_and_continue': True,
                    }
                    return render(
                        request,
                        self.change_form_template or [
                            f"admin/{self.model._meta.app_label}/{self.model._meta.model_name}/change_form.html",
                            "admin/change_form.html",
                        ],
                        context,
                    )
            
            elif 'save_rates' in request.POST:
                age_ranges = request.session.get('generated_ranges', [])
                bulk_form = MortalityRateBulkForm(request.POST, age_ranges=age_ranges)
                
                if bulk_form.is_valid():
                    try:
                        for i, range_data in enumerate(age_ranges):
                            rate_value = bulk_form.cleaned_data[f'rate_{i}']
                            MortalityRate.objects.create(
                                age_group_start=range_data['start'],
                                age_group_end=range_data['end'],
                                rate=rate_value
                            )
                        messages.success(request, 'Mortality rates created successfully.')
                        return HttpResponseRedirect(
                            reverse('admin:app_mortalityrate_changelist')
                        )
                    except Exception as e:
                        messages.error(request, f'Error saving rates: {str(e)}')

        # Default behavior for GET requests
        generator_form = MortalityRateGeneratorForm()
        context = {
            'form': form,
            'generator_form': generator_form,
            'show_generator': True,
            'opts': self.model._meta,
            'add': True,
            'is_popup': False,
            'save_as': False,
            'has_delete_permission': False,
            'has_add_permission': True,
            'has_change_permission': True,
            'show_save': True,
            'show_save_and_continue': True,
        }
        return render(
            request,
            self.change_form_template or [
                f"admin/{self.model._meta.app_label}/{self.model._meta.model_name}/change_form.html",
                "admin/change_form.html",
            ],
            context,
        )

#Loan Admin
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin, BranchFilterMixin):
    list_display = ('policy_holder', 'loan_amount', 'remaining_balance', 'accrued_interest', 'loan_status', 'created_at')
    readonly_fields = ('remaining_balance', 'accrued_interest', 'last_interest_date')
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name')
    
#Loan Repayment Admin
@admin.register(LoanRepayment)
class LoanRepaymentAdmin(BranchFilterMixin, admin.ModelAdmin):
    list_display = ('loan', 'amount', 'repayment_type', 'repayment_date', 'remaining_loan_balance')
    readonly_fields = ('remaining_loan_balance',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_code', 'email', 'is_active')
    search_fields = ('name', 'company_code')
    list_filter = ('is_active',)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch_code', 'location')
    search_fields = ('name', 'branch_code')
    list_filter = ('location',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(branch=request.user.profile.branch)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "branch" and not request.user.is_superuser:
            kwargs["queryset"] = branch.objects.filter(id=request.user.profile.branch.id)
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
    list_display = ('username', 'email', 'is_superuser', 'get_branch')
    search_fields = ('username', 'email')
    list_filter = ('is_superuser', 'is_active')

    def get_branch(self, obj):
        return obj.profile.branch.name if hasattr(obj, 'profile') and obj.profile.branch else "Not Assigned"
    get_branch.short_description = 'Branch'
    

    def save_model(self, request, obj, form, change):
        creating = not obj.pk
        super().save_model(request, obj, form, change)
        
        if creating and not obj.is_superuser:
            # For new non-superuser, try to assign first company
            first_company = Company.objects.first()
            if first_company:
                obj.profile.company = first_company
                obj.profile.save()
    