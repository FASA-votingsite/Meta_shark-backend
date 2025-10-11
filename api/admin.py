from django.contrib import admin
from .models import *

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'package_type', 'price', 'referral_bonus', 'daily_login_bonus']
    list_filter = ['package_type']

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['coupon_code', 'package', 'is_used', 'used_by', 'created_at']
    list_filter = ['is_used', 'package', 'created_at']
    actions = ['generate_coupons']
    
    def generate_coupons(self, request, queryset):
        for package in queryset:
            Coupon.generate_coupon(package)
        self.message_user(request, "Coupons generated successfully")
    generate_coupons.short_description = "Generate coupons for selected packages"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'wallet_balance', 'total_earnings', 'referral_code']
    list_filter = ['package']

@admin.register(ContentSubmission)
class ContentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'status', 'earnings', 'submission_date']
    list_filter = ['status', 'platform', 'submission_date']
    actions = ['approve_submissions', 'reject_submissions']
    
    def approve_submissions(self, request, queryset):
        for submission in queryset:
            submission.status = 'approved'
            submission.save()
        self.message_user(request, "Selected submissions approved")
    
    def reject_submissions(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, "Selected submissions rejected")

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'bank_name', 'status', 'priority', 'created_at']
    list_filter = ['status', 'created_at']
    actions = ['process_withdrawals', 'complete_withdrawals']
    
    def process_withdrawals(self, request, queryset):
        queryset.update(status='processing')
        self.message_user(request, "Selected withdrawals marked as processing")
    
    def complete_withdrawals(self, request, queryset):
        for withdrawal in queryset:
            withdrawal.status = 'completed'
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
        self.message_user(request, "Selected withdrawals completed")

admin.site.register(Referral)
admin.site.register(GameParticipation)
admin.site.register(Transaction)