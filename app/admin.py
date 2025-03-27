from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db import models
from django import forms
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.utils.html import format_html, mark_safe
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.db.models.signals import post_save
from datetime import date, datetime, timedelta
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.admin import site
from django.db.models import Sum, Count, Avg
from .views import manage_mortality_rates  
from .frontend_data import *
from .models import (
    InsurancePolicy, SalesAgent, PolicyHolder, Underwriting,
    ClaimRequest, ClaimProcessing, PremiumPayment,MortalityRate,
    EmployeePosition, Employee, PaymentProcessing, Branch, Company, AgentReport, AgentApplication, Occupation, DurationFactor, GSVRate, SSVConfig, Bonus, BonusRate, Loan, LoanRepayment,UserProfile, OTP, Commission, PolicySurrender, PolicyRenewal
)
from decimal import Decimal
import logging
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from django.utils import timezone, translation
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
import os
import uuid
from django.db.models import Sum, Q, Count, F, Value, FloatField
from django.db.models.functions import Cast, Coalesce, Concat
import csv
import calendar

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

#Bonus Rate Admin
@admin.register(BonusRate)
class BonusRateAdmin(admin.ModelAdmin):
    list_display = ('year', 'policy_type', 'min_year', 'max_year', 'bonus_per_thousand')
    ordering = ['year', 'policy_type', 'min_year']
    search_fields = ('year', 'policy_type')
    list_filter = ('year', 'policy_type')

# Register Duration Factor
@admin.register(DurationFactor)
class DurationFactorAdmin(admin.ModelAdmin):
    list_display = ( 'policy_type', 'min_duration', 'max_duration', 'factor')
    list_filter = ( 'policy_type', 'factor')
    search_fields = ('company__name',)

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
    
class PolicySurrenderAdmin(admin.ModelAdmin):
    list_display = ['policy_holder', 'request_date', 'surrender_type', 'status', 
                  'surrender_amount', 'gsv_amount', 'ssv_amount', 'payment_date', 'print_button']
    list_filter = ['status', 'surrender_type', 'request_date']
    search_fields = ['policy_holder__first_name', 'policy_holder__last_name', 'policy_holder__policy_number']
    readonly_fields = ['request_date', 'gsv_amount', 'ssv_amount', 'outstanding_loans', 
                     'processing_fee', 'tax_deduction', 'surrender_amount', 'approved_by']
    fieldsets = (
        ('Policy Information', {
            'fields': ('policy_holder', 'surrender_type', 'status', 'surrender_reason')
        }),
        ('Surrender Values', {
            'fields': ('gsv_amount', 'ssv_amount', 'outstanding_loans', 
                    'processing_fee', 'tax_deduction', 'surrender_amount')
        }),
        ('Approval & Payment', {
            'fields': ('approved_by', 'approval_date', 'payment_date', 'payment_method', 'notes')
        }),
    )
    
    actions = ['approve_selected_surrenders', 'process_payment_for_selected']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'print-surrender/<int:surrender_id>/',
                self.admin_site.admin_view(self.print_surrender_certificate),
                name='print-surrender-certificate',
            ),
        ]
        return custom_urls + urls
    
    def print_surrender_certificate(self, request, surrender_id):
        """View to print surrender certificate"""
        try:
            surrender = PolicySurrender.objects.get(pk=surrender_id)
            policy_holder = surrender.policy_holder
            
            # Get company info
            company_name = policy_holder.branch.company.name if policy_holder.branch and policy_holder.branch.company else "Insurance Company"
            company_logo = policy_holder.branch.company.logo if policy_holder.branch and policy_holder.branch.company else None
            company_address = policy_holder.branch.company.address if policy_holder.branch and policy_holder.branch.company else None
            
            context = {
                'title': 'Policy Surrender Certificate',
                'surrender': surrender,
                'policy_holder': policy_holder,
                'company_name': company_name,
                'company_logo': company_logo,
                'company_address': company_address,
            }
            
            return TemplateResponse(
                request,
                'surrender/print.html',
                context,
            )
        except PolicySurrender.DoesNotExist:
            messages.error(request, "Surrender record not found.")
            return redirect('admin:app_policysurrender_changelist')
    
    def approve_selected_surrenders(self, request, queryset):
        """Admin action to approve selected surrender requests"""
        success_count = 0
        failure_count = 0
        errors = []
        
        for surrender in queryset.filter(status__in=['Pending', 'Processed']):
            try:
                surrender.approve_surrender(request.user)
                success_count += 1
            except Exception as e:
                failure_count += 1
                errors.append(f"{surrender.policy_holder}: {str(e)}")
        
        if success_count > 0:
            self.message_user(request, f"Successfully approved {success_count} surrender requests.", level=messages.SUCCESS)
        
        if failure_count > 0:
            error_message = f"Failed to approve {failure_count} surrender requests."
            if len(errors) <= 3:  # Show detailed errors for a few failures
                error_message += " Errors: " + "; ".join(errors)
            self.message_user(request, error_message, level=messages.ERROR)
        
        if success_count == 0 and failure_count == 0:
            self.message_user(request, "No surrenders were found to approve.", level=messages.WARNING)
    
    def process_payment_for_selected(self, request, queryset):
        """Admin action to mark selected surrenders as paid"""
        success_count = 0
        failure_count = 0
        errors = []
        
        for surrender in queryset.filter(status='Approved'):
            try:
                surrender.process_payment('Bank Transfer')
                success_count += 1
            except Exception as e:
                failure_count += 1
                errors.append(f"{surrender.policy_holder}: {str(e)}")
        
        if success_count > 0:
            self.message_user(request, f"Successfully processed payment for {success_count} surrender requests.", level=messages.SUCCESS)
        
        if failure_count > 0:
            error_message = f"Failed to process payment for {failure_count} surrender requests."
            if len(errors) <= 3:  # Show detailed errors for a few failures
                error_message += " Errors: " + "; ".join(errors)
            self.message_user(request, error_message, level=messages.ERROR)
        
        if success_count == 0 and failure_count == 0:
            self.message_user(request, "No surrenders were found to process payments.", level=messages.WARNING)
        
    process_payment_for_selected.short_description = "Process payment for selected surrenders"
    
    def print_button(self, obj):
        """Generate print button for surrenders"""
        if obj and obj.pk and obj.status in ['Approved', 'Processed']:
            url = reverse('admin:print-surrender-certificate', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color:#2980b9;color:white;padding:6px 12px;border-radius:4px;text-decoration:none;display:inline-block;font-weight:bold;text-align:center;">'
                '<i class="fas fa-print" style="margin-right:5px;"></i> Print</a>',
                url
            )
        return ""
    print_button.short_description = ""
    
    def save_model(self, request, obj, form, change):
        """Override save_model to handle approval"""
        original_status = None
        
        # Get original status if this is an update
        if change:
            original = PolicySurrender.objects.get(pk=obj.pk)
            original_status = original.status
        
        # If status changed to Approved, approve the surrender
        if change and original_status != 'Approved' and obj.status == 'Approved':
            try:
                obj.approve_surrender(request.user)
            except ValidationError as e:
                messages.error(request, str(e))
                # Reset status to original to prevent partially approved state
                obj.status = original_status
                # Don't call super().save_model since we don't want to save the invalid status
                return
        # If status changed to Processed, process payment
        elif change and original_status == 'Approved' and obj.status == 'Processed':
            try:
                obj.process_payment(obj.payment_method or 'Bank Transfer')
            except ValidationError as e:
                messages.error(request, str(e))
                obj.status = original_status
                return
        
        # For all other cases or if approval/processing succeeded
        super().save_model(request, obj, form, change)

    approve_selected_surrenders.short_description = "Approve selected surrender requests"

# Register models
admin.site.register(PolicySurrender, PolicySurrenderAdmin)

class PolicyRenewalAdmin(admin.ModelAdmin):
    list_display = ['policy_holder', 'due_date', 'grace_period_end', 'renewal_amount', 'status', 'reminder_status', 'actions_column']
    list_filter = ['status', 'due_date', 'is_first_reminder_sent', 'is_second_reminder_sent', 'is_final_reminder_sent']
    search_fields = ['policy_holder__policy_number', 'policy_holder__first_name', 'policy_holder__last_name']
    readonly_fields = ['is_first_reminder_sent', 'first_reminder_date', 'is_second_reminder_sent', 'second_reminder_date', 'is_final_reminder_sent', 'final_reminder_date']
    autocomplete_fields = ['policy_holder']
    ordering = ['-due_date']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'renew/<int:renewal_id>/',
                self.admin_site.admin_view(self.renew_policy),
                name='renew-policy',
            ),
            path(
                'send-reminder/<int:renewal_id>/<str:reminder_type>/',
                self.admin_site.admin_view(self.send_reminder),
                name='send-renewal-reminder',
            ),
        ]
        return custom_urls + urls
        
    def reminder_status(self, obj):
        """Display reminder status with badges."""
        if obj.is_final_reminder_sent:
            return format_html('<span style="background-color: #e74c3c; color: white; padding: 3px 6px; border-radius: 3px;">Final sent</span>')
        elif obj.is_second_reminder_sent:
            return format_html('<span style="background-color: #f39c12; color: white; padding: 3px 6px; border-radius: 3px;">Second sent</span>')
        elif obj.is_first_reminder_sent:
            return format_html('<span style="background-color: #3498db; color: white; padding: 3px 6px; border-radius: 3px;">First sent</span>')
        else:
            return format_html('<span style="background-color: #95a5a6; color: white; padding: 3px 6px; border-radius: 3px;">No reminders</span>')
            
    reminder_status.short_description = 'Reminders'
    
    def actions_column(self, obj):
        """Display action buttons based on status."""
        buttons = []
        
        # Complete renewal button
        if obj.status == 'Pending':
            buttons.append(f'<a class="button" href="{reverse("admin:renew-policy", args=[obj.pk])}" style="background-color: #2ecc71;">Complete Renewal</a>')
            
        # Reminder buttons
        if obj.status == 'Pending':
            if not obj.is_first_reminder_sent:
                buttons.append(f'<a class="button" href="{reverse("admin:send-renewal-reminder", args=[obj.pk, "first"])}" style="background-color: #3498db;">Send First Reminder</a>')
            elif not obj.is_second_reminder_sent:
                buttons.append(f'<a class="button" href="{reverse("admin:send-renewal-reminder", args=[obj.pk, "second"])}" style="background-color: #f39c12;">Send Second Reminder</a>')
            elif not obj.is_final_reminder_sent:
                buttons.append(f'<a class="button" href="{reverse("admin:send-renewal-reminder", args=[obj.pk, "final"])}" style="background-color: #e74c3c;">Send Final Reminder</a>')
                
        return format_html('<div style="display: flex; gap: 5px;">{}</div>', mark_safe(''.join(buttons)))
        
    actions_column.short_description = 'Actions'
    
    def send_reminder(self, request, renewal_id, reminder_type):
        """View to send renewal reminders to policy holders."""
        renewal = self.get_object(request, renewal_id)
        
        if renewal is None:
            messages.error(request, "Renewal not found.")
            return redirect('admin:app_policyrenewal_changelist')
            
        if renewal.status != 'Pending':
            messages.error(request, f"Cannot send reminder for {renewal.get_status_display()} renewal.")
            return redirect('admin:app_policyrenewal_change', renewal_id)
            
        # Validate reminder type
        valid_types = ['first', 'second', 'final']
        if reminder_type not in valid_types:
            messages.error(request, f"Invalid reminder type: {reminder_type}")
            return redirect('admin:app_policyrenewal_change', renewal_id)
            
        # Check if current reminder type can be sent based on sequence
        if reminder_type == 'second' and not renewal.is_first_reminder_sent:
            messages.error(request, "Cannot send second reminder before sending first reminder.")
            return redirect('admin:app_policyrenewal_change', renewal_id)
            
        if reminder_type == 'final' and not renewal.is_second_reminder_sent:
            messages.error(request, "Cannot send final reminder before sending second reminder.")
            return redirect('admin:app_policyrenewal_change', renewal_id)
            
        # Send the reminder
        if renewal.send_reminder(reminder_type):
            messages.success(request, f"Sent {reminder_type} reminder to {renewal.policy_holder.first_name} {renewal.policy_holder.last_name}.")
        else:
            messages.error(request, f"Failed to send {reminder_type} reminder.")
            
        return redirect('admin:app_policyrenewal_change', renewal_id)
    
    def renew_policy(self, request, renewal_id):
        """View to renew a policy"""
        renewal = self.get_object(request, renewal_id)
        
        if request.method == 'POST':
            notes = request.POST.get('notes', '')
            
            if renewal.mark_as_renewed(request.user):
                # Update notes
                renewal.notes = notes
                renewal.save(update_fields=['notes'])
                
                messages.success(request, f"Policy {renewal.policy_holder.policy_number} has been renewed successfully.")
                return redirect('admin:app_policyrenewal_changelist')
            else:
                messages.error(request, f"Failed to renew policy {renewal.policy_holder.policy_number}.")
        
        # Get policy details for context
        policy_holder = renewal.policy_holder
        premium_payment = policy_holder.premium_payments.first()
        
        context = {
            'title': f'Renew Policy: {policy_holder.policy_number}',
            'renewal': renewal,
            'policy_holder': policy_holder,
            'premium_payment': premium_payment,
            'opts': self.model._meta,
        }
        
        return TemplateResponse(
            request,
            'admin/app/policyrenewal/renewal_form.html',
            context,
        )

# Register models
admin.site.register(PolicyRenewal, PolicyRenewalAdmin)

# Register PolicyHolder

@admin.register(PolicyHolder)
class PolicyHolderAdmin(BranchFilterMixin, admin.ModelAdmin):
    list_display = ('policy_number', 'first_name', 'last_name', 'status', 'policy', 'sum_assured', 'payment_interval')
    search_fields = ('first_name', 'last_name', 'policy_number')
    list_filter = ('status', 'policy', 'occupation')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        branch = getattr(request.user.profile, 'branch', None)
        return qs.filter(branch=branch) if branch else qs.none()

    