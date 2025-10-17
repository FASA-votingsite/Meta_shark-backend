from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.contrib import messages
import random
import string
from .models import *

class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code', 'package_info', 'status', 'used_by_info', 'created_at', 'copy_button')
    list_filter = ('package', 'is_used', 'created_at')
    search_fields = ('coupon_code', 'used_by__username')
    readonly_fields = ('created_at', 'used_at', 'coupon_code')
    list_per_page = 25
    
    # FIXED: Define actions as a list of method names
    actions = ['generate_pro_coupon_admin_action', 'generate_silver_coupon_admin_action']
    
    def package_info(self, obj):
        if obj.package:
            return format_html(
                '<strong>{}</strong><br><small>₦{}</small>',
                obj.package.name,
                obj.package.price
            )
        return "No Package"
    package_info.short_description = 'Package'
    
    def status(self, obj):
        if obj.is_used:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">❌ Used</span>'
            )
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">✅ Available</span>'
        )
    status.short_description = 'Status'
    
    def used_by_info(self, obj):
        if obj.used_by:
            return format_html(
                '{}<br><small>{}</small>',
                obj.used_by.username,
                obj.used_by.email
            )
        return "—"
    used_by_info.short_description = 'Used By'
    
    def copy_button(self, obj):
        return format_html(
            '<button type="button" class="copy-coupon-btn" data-coupon="{}" '
            'style="padding: 6px 12px; background: #417690; color: white; '
            'border: none; border-radius: 4px; cursor: pointer; font-size: 12px; '
            'margin: 2px;">📋 Copy</button>'
            '<span id="copy-status-{}" style="margin-left: 8px; font-size: 11px; color: green;"></span>',
            obj.coupon_code, obj.coupon_code
        )
    copy_button.short_description = 'Actions'
    
    # Admin actions (for the actions dropdown)
    def generate_pro_coupon_admin_action(self, request, queryset):
        """Admin action to generate Pro coupon"""
        return self._generate_coupon_admin_action(request, 'pro')
    generate_pro_coupon_admin_action.short_description = "🎁 Generate Pro Coupon"
    
    def generate_silver_coupon_admin_action(self, request, queryset):
        """Admin action to generate Silver coupon"""
        return self._generate_coupon_admin_action(request, 'silver')
    generate_silver_coupon_admin_action.short_description = "🎁 Generate Silver Coupon"
    
    def _generate_coupon_admin_action(self, request, package_type):
        """Helper method for admin actions"""
        try:
            package = Package.objects.get(package_type=package_type)
            coupon = self._create_coupon(package)
            
            message = format_html(
                '✅ <strong>{} Coupon Generated!</strong><br>'
                'Code: <code style="background: #f8f9fa; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}</code>',
                package_type.title(),
                coupon.coupon_code
            )
            self.message_user(request, message, messages.SUCCESS)
            
        except Package.DoesNotExist:
            self.message_user(
                request,
                f'❌ {package_type.title()} package not found. Please create it first.',
                messages.ERROR
            )
        
        # Return None to stay on the same page (Django admin expectation)
        return None
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-pro-coupon/', self.admin_site.admin_view(self.generate_pro_coupon_view), name='generate_pro_coupon'),
            path('generate-silver-coupon/', self.admin_site.admin_view(self.generate_silver_coupon_view), name='generate_silver_coupon'),
        ]
        return custom_urls + urls
    
    def generate_pro_coupon_view(self, request):
        return self._generate_coupon_view(request, 'pro')
    
    def generate_silver_coupon_view(self, request):
        return self._generate_coupon_view(request, 'silver')
    
    def _generate_coupon_view(self, request, package_type):
        try:
            package = Package.objects.get(package_type=package_type)
            coupon = self._create_coupon(package)
            
            message = format_html(
                '✅ <strong>{} Coupon Generated!</strong><br>'
                'Code: <code style="background: #f8f9fa; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}</code><br>'
                'Package: {} (₦{})',
                package_type.title(),
                coupon.coupon_code,
                package.name,
                package.price
            )
            messages.success(request, message)
            
        except Package.DoesNotExist:
            messages.error(
                request,
                f'❌ {package_type.title()} package not found. Please create it in the Packages section first.'
            )
        
        return HttpResponseRedirect(reverse('admin:api_coupon_changelist'))
    
    def _create_coupon(self, package):
        prefix_map = {
            'pro': 'METAPRO',
            'silver': 'METASIL'
        }
        prefix = prefix_map.get(package.package_type, 'META')
        
        # Generate unique coupon code
        attempts = 0
        while attempts < 10:
            random_digits = ''.join(random.choices(string.digits, k=6))
            coupon_code = f"{prefix}{random_digits}"
            if not Coupon.objects.filter(coupon_code=coupon_code).exists():
                break
            attempts += 1
        else:
            import time
            timestamp = str(int(time.time()))[-6:].zfill(6)
            coupon_code = f"{prefix}{timestamp}"
        
        return Coupon.objects.create(
            coupon_code=coupon_code,
            package=package,
            price_paid=package.price
        )

    class Media:
        js = ('admin/js/coupon_copy.js',)

# UserProfileAdmin
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'user_email', 'package_name', 'phone_number', 'wallet_display', 'referral_code')
    list_filter = ('package',)
    search_fields = ('user__username', 'phone_number', 'user__email')
    readonly_fields = ('referral_code', 'user', 'wallet_balance', 'total_earnings')
    
    def username(self, obj):
        return obj.user.username if obj.user else "—"
    username.short_description = 'Username'
    username.admin_order_field = 'user__username'
    
    def user_email(self, obj):
        return obj.user.email if obj.user else "—"
    user_email.short_description = 'Email'
    
    def package_name(self, obj):
        return obj.package.name if obj.package else "—"
    package_name.short_description = 'Package'
    
    def wallet_display(self, obj):
        return f"₦{obj.wallet_balance:.2f}" if obj.wallet_balance else "₦0.00"
    wallet_display.short_description = 'Wallet Balance'

# PackageAdmin
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'package_type', 'price_display', 'referral_bonus_display', 'daily_login_bonus_display')
    list_filter = ('package_type',)
    
    def price_display(self, obj):
        return f"₦{obj.price:.2f}"
    price_display.short_description = 'Price'
    
    def referral_bonus_display(self, obj):
        return f"₦{obj.referral_bonus:.2f}"
    referral_bonus_display.short_description = 'Referral Bonus'
    
    def daily_login_bonus_display(self, obj):
        return f"₦{obj.daily_login_bonus:.2f}"
    daily_login_bonus_display.short_description = 'Daily Login Bonus'

# ContentSubmissionAdmin
class ContentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('username', 'platform', 'status_badge', 'earnings_display', 'submission_date')
    list_filter = ('platform', 'status', 'submission_date')
    search_fields = ('user__username', 'description')
    readonly_fields = ('submission_date',)
    
    def username(self, obj):
        return obj.user.username if obj.user else "No User"
    username.short_description = 'User'
    username.admin_order_field = 'user__username'
    
    def status_badge(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'approved': '#28a745', 
            'rejected': '#dc3545',
            'paid': '#17a2b8'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def earnings_display(self, obj):
        return f"₦{obj.earnings:.2f}" if obj.earnings else "₦0.00"
    earnings_display.short_description = 'Earnings'

# ReferralAdmin
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer_name', 'referee_name', 'referral_date', 'reward_earned_display', 'is_paid_badge')
    list_filter = ('referral_date', 'is_paid')
    
    def referrer_name(self, obj):
        return obj.referrer.username if obj.referrer else "No Referrer"
    referrer_name.short_description = 'Referrer'
    
    def referee_name(self, obj):
        return obj.referee.username if obj.referee else "No Referee"
    referee_name.short_description = 'Referee'
    
    def reward_earned_display(self, obj):
        return f"₦{obj.reward_earned:.2f}" if obj.reward_earned else "₦0.00"
    reward_earned_display.short_description = 'Reward'
    
    def is_paid_badge(self, obj):
        if obj.is_paid:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">PAID</span>'
            )
        return format_html(
            '<span style="background: #ffc107; color: black; padding: 4px 8px; border-radius: 12px; font-size: 12px;">PENDING</span>'
        )
    is_paid_badge.short_description = 'Payment Status'

# GameParticipationAdmin
class GameParticipationAdmin(admin.ModelAdmin):
    list_display = ('username', 'game_type_badge', 'participation_date', 'reward_earned_display')
    list_filter = ('game_type', 'participation_date')
    
    def username(self, obj):
        return obj.user.username if obj.user else "No User"
    username.short_description = 'User'
    
    def game_type_badge(self, obj):
        game_colors = {
            'daily_spin': '#17a2b8',
            'scratch_card': '#e83e8c',
            'quiz': '#20c997'
        }
        color = game_colors.get(obj.game_type, '#6c757d')
        display_name = obj.get_game_type_display()
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            display_name
        )
    game_type_badge.short_description = 'Game Type'
    
    def reward_earned_display(self, obj):
        return f"₦{obj.reward_earned:.2f}" if obj.reward_earned else "₦0.00"
    reward_earned_display.short_description = 'Reward'

# TransactionAdmin
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('username', 'amount_display', 'transaction_type_badge', 'date', 'description_short')
    list_filter = ('transaction_type', 'date')
    search_fields = ('user__username', 'description')
    
    def username(self, obj):
        return obj.user.username if obj.user else "No User"
    username.short_description = 'User'
    
    def amount_display(self, obj):
        color = '#28a745' if obj.amount > 0 else '#dc3545'
        symbol = '+' if obj.amount > 0 else ''
        return format_html(
            '<span style="color: {}; font-weight: bold;">₦{}{:.2f}</span>',
            color,
            symbol,
            abs(obj.amount)
        )
    amount_display.short_description = 'Amount'
    
    def transaction_type_badge(self, obj):
        type_colors = {
            'content': '#17a2b8',
            'referral': '#20c997',
            'game': '#e83e8c',
            'daily_login': '#6f42c1',
            'payout': '#fd7e14',
            'package_purchase': '#343a40'
        }
        color = type_colors.get(obj.transaction_type, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_transaction_type_display().upper()
        )
    transaction_type_badge.short_description = 'Type'
    
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

# WithdrawalRequestAdmin
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('username', 'amount_display', 'bank_name', 'account_number', 'status_badge', 'created_at', 'priority_badge')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'bank_name', 'account_number')
    
    def username(self, obj):
        return obj.user.username if obj.user else "No User"
    username.short_description = 'User'
    
    def amount_display(self, obj):
        return f"₦{obj.amount:.2f}"
    amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        priority_colors = {
            1: '#dc3545',  # High priority
            2: '#ffc107',  # Medium priority  
            3: '#28a745',  # Low priority
        }
        color = priority_colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">Priority {}</span>',
            color,
            obj.priority
        )
    priority_badge.short_description = 'Priority'

# Register all models with their admin classes
admin.site.register(Package, PackageAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(ContentSubmission, ContentSubmissionAdmin)
admin.site.register(Referral, ReferralAdmin)
admin.site.register(GameParticipation, GameParticipationAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(WithdrawalRequest, WithdrawalRequestAdmin)

# Admin site customization
admin.site.site_header = "🎯 META_SHARK Admin"
admin.site.site_title = "META_SHARK Administration"
admin.site.index_title = "📊 Dashboard"