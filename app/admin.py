from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db import models
from django import forms
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.db.models.signals import post_save
from datetime import date, datetime, timedelta
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.admin import site
from django.db.models import Sum
from .views import manage_mortality_rates  
from .frontend_data import *
from .models import (
    InsurancePolicy, SalesAgent, PolicyHolder, Underwriting,
    ClaimRequest, ClaimProcessing, PremiumPayment,MortalityRate,
    EmployeePosition, Employee, PaymentProcessing, Branch, Company, AgentReport, AgentApplication, Occupation, DurationFactor, GSVRate, SSVConfig, Bonus, BonusRate, Loan, LoanRepayment,UserProfile, OTP, Commission
)
from decimal import Decimal
import logging
from django.utils.translation import gettext_lazy as _


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
    readonly_fields = ( 'accrued_amount', 'start_date', 'last_updated', 'total_bonus_accrued')

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
                    'payment_interval', 'occupation', 'maturity_date', 'print_button')
    search_fields = ('first_name', 'last_name','policy_number')
    list_filter = ('status', 'policy', 'occupation')
    inlines = [BonusInline, UnderwritingInline]
    # change_form_template = 'policyholder/change_form.html'
    
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
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'print/<path:object_id>/',
                self.admin_site.admin_view(self.print_policy),
                name='print_policy',
            ),
        ]
        return custom_urls + urls
    
    def print_policy(self, request, object_id):
        try:
            policyholder = self.get_object(request, object_id)
            company_name = policyholder.branch.company.name if policyholder.branch and policyholder.branch.company else "Insurance Company"
            
            context = {
                'title': f'Policy #{policyholder.policy_number}',
                'original': policyholder,
                'company_name': company_name,
                'opts': self.model._meta,
                'media': self.media,
            }
            
            return render(request, 'policyholder/print.html', context)
        except (PolicyHolder.DoesNotExist, ValidationError):
            return redirect('admin:app_policyholder_changelist')

    def print_button(self, obj):
        return format_html(
            '<a class="button btn btn-info btn-sm" href="{}" onclick="window.open(this.href, \'_blank\', \'width=800,height=600\').print(); return false;">Print</a>',
            reverse('admin:print_policy', args=[obj.pk])
        )
    print_button.short_description = 'Print'

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
    list_display = ('policy_holder', 'claim_date', 'status', 'claim_amount', 'print_button')
    readonly_fields = ('claim_amount',)
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/print/',
                self.admin_site.admin_view(self.print_claim),
                name='print_claim_request',
            ),
        ]
        return custom_urls + urls
    
    def print_claim(self, request, object_id):
        try:
            claim = self.get_object(request, object_id)
            company_name = claim.policy_holder.branch.company.name if claim.policy_holder.branch and claim.policy_holder.branch.company else "Insurance Company"
            
            context = {
                'title': f'Claim #{claim.id}',
                'original': claim,
                'company_name': company_name,
                'opts': self.model._meta,
                'media': self.media,
            }
            
            return render(request, 'claim/print.html', context)
        except (ClaimRequest.DoesNotExist, ValidationError):
            return redirect('admin:app_claimrequest_changelist')
    
    def print_button(self, obj):
        return format_html(
            '<a class="button btn btn-info btn-sm" href="{}" onclick="window.open(this.href, \'_blank\', \'width=800,height=600\').print(); return false;">Print</a>',
            reverse('admin:print_claim_request', args=[obj.pk])
        )
    print_button.short_description = 'Print'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs


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
        'total_paid', 'fine_due', 'fine_paid', 'payment_status', 'next_payment_date'
    )
    list_filter = ('payment_status', 'policy_holder__payment_interval')
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name', 'policy_holder__policy_number')
    readonly_fields = (
        'annual_premium', 'interval_payment', 'total_premium',
        'remaining_premium','total_paid', 'fine_paid', 'gsv_value', 'ssv_value'
    )
    
    actions = ['add_payment', 'check_policy_expiry']

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

    @admin.action(description="Record payment for selected items")
    def add_payment(self, request, queryset):
        update_count = 0
        error_count = 0
        for payment in queryset:
            try:
                # Calculate any applicable fine
                fine = payment.calculate_fine()
                
                # Add the current interval payment plus any fine
                payment_amount = payment.interval_payment
                if fine > Decimal('0.00'):
                    payment_amount += fine  # Include fine in payment
                    self.message_user(
                        request,
                        f"Fine of {fine} included for {payment.policy_holder}.",
                        level=messages.INFO
                    )
                
                # Check for policy expiry first
                if payment.check_policy_expiry():
                    self.message_user(
                        request, 
                        f"Policy for {payment.policy_holder} has expired due to non-payment for over 3 years.", 
                        level=messages.WARNING
                    )
                    error_count += 1
                    continue
                    
                # Validate if the period is already paid
                if payment.is_current_period_paid():
                    self.message_user(
                        request, 
                        f"Payment for {payment.policy_holder} was skipped: current period already paid.", 
                        level=messages.WARNING
                    )
                    error_count += 1
                    continue
                
                # Use the model's add_payment method
                if payment.add_payment(payment_amount):
                    update_count += 1
                    
                    # Update the next payment date
                    if payment.policy_holder.payment_interval != "Single":
                        interval_months = {
                            "quarterly": 3,
                            "semi_annual": 6,
                            "annual": 12
                        }.get(payment.policy_holder.payment_interval)
                        
                        if payment.next_payment_date:
                            payment.next_payment_date = payment.next_payment_date.replace(
                                month=((payment.next_payment_date.month - 1 + interval_months) % 12) + 1,
                                year=payment.next_payment_date.year + ((payment.next_payment_date.month - 1 + interval_months) // 12)
                            )
                        else:
                            today = date.today()
                            payment.next_payment_date = today.replace(
                                month=((today.month - 1 + interval_months) % 12) + 1,
                                year=today.year + ((today.month - 1 + interval_months) // 12)
                            )
                        
                        payment.save()
                        
                    # Display total amount paid including any fine
                    self.message_user(
                        request,
                        f"Payment of {payment_amount} recorded for {payment.policy_holder}.",
                        level=messages.SUCCESS
                    )
            except ValidationError as e:
                self.message_user(
                    request, 
                    f"Error recording payment for {payment.policy_holder}: {str(e)}", 
                    level=messages.ERROR
                )
                error_count += 1
            except Exception as e:
                self.message_user(
                    request, 
                    f"Unexpected error for {payment.policy_holder}: {str(e)}", 
                    level=messages.ERROR
                )
                error_count += 1
                
        message = []
        if update_count > 0:
            message.append(f"Successfully recorded payments for {update_count} items.")
        if error_count > 0:
            message.append(f"Failed to record payments for {error_count} items.")
            
        if message:
            self.message_user(
                request,
                " ".join(message),
                messages.SUCCESS if error_count == 0 else messages.WARNING,
            )

    @admin.action(description="Check selected policies for expiry")
    def check_policy_expiry(self, request, queryset):
        """Admin action to check if policies have expired due to non-payment"""
        checked_count = 0
        expired_count = 0
        
        for payment in queryset:
            checked_count += 1
            if payment.check_policy_expiry():
                # Save to persist the 'Expired' status set in check_policy_expiry
                payment.save(update_fields=['payment_status'])
                expired_count += 1
                
        if expired_count > 0:
            self.message_user(
                request,
                f"Checked {checked_count} policies. {expired_count} policies marked as expired due to non-payment.",
                messages.WARNING
            )
        else:
            self.message_user(
                request,
                f"Checked {checked_count} policies. No expired policies found.",
                messages.SUCCESS
            )


            


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
    list_display = ('id', 'first_name', 'last_name', 'branch', 'email', 'phone_number', 'status', 'created_at', 'print_button')
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
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/print/',
                self.admin_site.admin_view(self.print_application),
                name='print_agent_application',
            ),
        ]
        return custom_urls + urls
    
    def print_application(self, request, object_id):
        try:
            application = self.get_object(request, object_id)
            company_name = application.branch.company.name if application.branch and application.branch.company else "Insurance Company"
            
            context = {
                'title': f'Agent Application: {application.first_name} {application.last_name}',
                'original': application,
                'company_name': company_name,
                'opts': self.model._meta,
                'media': self.media,
            }
            
            return render(request, 'agentapplication/print.html', context)
        except (AgentApplication.DoesNotExist, ValidationError):
            return redirect('admin:app_agentapplication_changelist')
    
    def print_button(self, obj):
        return format_html(
            '<a class="button btn btn-info btn-sm" href="{}" onclick="window.open(this.href, \'_blank\', \'width=800,height=600\').print(); return false;">Print</a>',
            reverse('admin:print_agent_application', args=[obj.pk])
        )
    print_button.short_description = 'Print'
    
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
                        **site.each_context(request),
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
            **site.each_context(request),
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

class LoanRepaymentInline(admin.StackedInline):
    model = LoanRepayment
    extra = 1
    readonly_fields = ('repayment_date', 'remaining_loan_balance')
    fields = ('amount', 'repayment_type', 'repayment_date', 'remaining_loan_balance')
    can_delete = False

#Loan Admin
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin, BranchFilterMixin):
    list_display = ('policy_holder', 'loan_amount', 'remaining_balance', 'accrued_interest', 'loan_status', 'created_at', 'print_button')
    readonly_fields = ('remaining_balance', 'accrued_interest', 'last_interest_date')
    search_fields = ('policy_holder__first_name', 'policy_holder__last_name')
    inlines = [LoanRepaymentInline]
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/print/',
                self.admin_site.admin_view(self.print_loan),
                name='print_loan',
            ),
        ]
        return custom_urls + urls
    
    def print_loan(self, request, object_id):
        try:
            loan = self.get_object(request, object_id)
            company_name = loan.policy_holder.branch.company.name if loan.policy_holder.branch and loan.policy_holder.branch.company else "Insurance Company"
            
            # Get today's date and year for the footer
            current_date = date.today()
            current_year = current_date.year
            
            context = {
                'title': f'Loan #{loan.id}',
                'loan': loan,
                'company_name': company_name,
                'current_date': current_date,
                'current_year': current_year,
                'opts': self.model._meta,
                'media': self.media,
            }
            
            return render(request, 'loan/print.html', context)
        except (Loan.DoesNotExist, ValidationError):
            return redirect('admin:app_loan_changelist')
    
    def print_button(self, obj):
        return format_html(
            '<a class="button btn btn-info btn-sm" href="{}" onclick="window.open(this.href, \'_blank\', \'width=800,height=600\').print(); return false;">Print</a>',
            reverse('admin:print_loan', args=[obj.pk])
        )
    print_button.short_description = 'Print'

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_code', 'email', 'is_active')
    search_fields = ('name', 'company_code')
    list_filter = ('is_active',)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch_code', 'location', 'actions_buttons')
    search_fields = ('name', 'branch_code')
    list_filter = ('location',)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/report/<str:period>/',
                self.admin_site.admin_view(self.branch_report),
                name='branch_report',
            ),
        ]
        return custom_urls + urls
    
    def branch_report(self, request, object_id, period):
        try:
            branch = self.get_object(request, object_id)
            company_name = branch.company.name if branch.company else "Insurance Company"
            
            today = date.today()
            if period == 'weekly':
                start_date = today - timedelta(days=7)
                title = f"Weekly Report: {start_date.strftime('%b %d')} - {today.strftime('%b %d, %Y')}"
            elif period == 'monthly':
                # Get the first day of the current month
                start_date = today.replace(day=1)
                title = f"Monthly Report: {start_date.strftime('%B %Y')}"
            elif period == 'yearly':
                # Get the first day of the current year
                start_date = today.replace(month=1, day=1)
                title = f"Yearly Report: {start_date.strftime('%Y')}"
            else:
                # Default to last 30 days
                start_date = today - timedelta(days=30)
                title = f"30 Day Report: {start_date.strftime('%b %d')} - {today.strftime('%b %d, %Y')}"
            
            # Get policy holders for this branch in the date range
            policy_holders = PolicyHolder.objects.filter(
                branch=branch,
                start_date__gte=start_date,
                start_date__lte=today
            )
            
            # Get premium payments for this branch in the date range
            premium_payments = PremiumPayment.objects.filter(
                policy_holder__branch=branch,
                next_payment_date__gte=start_date
            )
            
            # Get claims for this branch in the date range
            claims = ClaimRequest.objects.filter(
                policy_holder__branch=branch,
                claim_date__gte=start_date,
                claim_date__lte=today
            )
            
            # Get loans for this branch in the date range
            loans = Loan.objects.filter(
                policy_holder__branch=branch,
                created_at__gte=start_date,
                created_at__lte=today
            )
            
            # Get agents for this branch
            agents = SalesAgent.objects.filter(branch=branch)
            # Get agent applications in the date range
            agent_applications = AgentApplication.objects.filter(
                branch=branch,
                created_at__gte=start_date,
                created_at__lte=today
            )
            
            # Calculate totals
            total_policies = policy_holders.count()
            total_premium = premium_payments.aggregate(total=Sum('paid_amount'))['total'] or 0
            total_claims = claims.aggregate(total=Sum('claim_amount'))['total'] or 0
            total_loans = loans.aggregate(total=Sum('loan_amount'))['total'] or 0
            
            context = {
                'title': title,
                'branch': branch,
                'company_name': company_name,
                'period': period,
                'start_date': start_date,
                'end_date': today,
                'total_policies': total_policies,
                'total_premium': total_premium,
                'total_claims': total_claims,
                'total_loans': total_loans,
                'policy_holders': policy_holders[:50],  # Limit to 50 for performance
                'premium_payments': premium_payments[:50],
                'claims': claims[:50],
                'loans': loans[:50],
                'agents': agents[:50],
                'agent_applications': agent_applications[:50],
                'report_date': today,
                'opts': self.model._meta,
                'media': self.media,
            }
            
            return render(request, 'branch/report.html', context)
        except (Branch.DoesNotExist, ValidationError):
            return redirect('admin:app_branch_changelist')
    
    def actions_buttons(self, obj):
        return format_html(
            '<div class="branch-actions">'
            '<a class="button btn btn-info btn-sm" href="{}" onclick="window.open(this.href, \'_blank\', \'width=800,height=600\').print(); return false;" title="Weekly Report">Weekly</a> '
            '<a class="button btn btn-success btn-sm" href="{}" onclick="window.open(this.href, \'_blank\', \'width=800,height=600\').print(); return false;" title="Monthly Report">Monthly</a> '
            '<a class="button btn btn-warning btn-sm" href="{}" onclick="window.open(this.href, \'_blank\', \'width=800,height=600\').print(); return false;" title="Yearly Report">Yearly</a>'
            '</div>',
            reverse('admin:branch_report', args=[obj.pk, 'weekly']),
            reverse('admin:branch_report', args=[obj.pk, 'monthly']),
            reverse('admin:branch_report', args=[obj.pk, 'yearly']),
        )
    actions_buttons.short_description = 'Reports'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(branch=request.user.profile.branch)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "branch" and not request.user.is_superuser:
            kwargs["queryset"] = Branch.objects.filter(id=request.user.profile.branch.id)
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

class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at', 'expires_at', 'is_used')
    search_fields = ('user__username', 'otp')
    list_filter = ('is_used', 'created_at')
    readonly_fields = ('created_at', 'expires_at')

# Register models
admin.site.register(OTP, OTPAdmin)

# Register Commission 
@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('agent', 'policy_holder', 'amount', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('agent__first_name', 'agent__last_name', 'policy_holder__policy_number')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            # Filter by branch if user has one
            return qs.filter(agent__branch=request.user.profile.branch)
        return qs
    
    