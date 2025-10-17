from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import secrets
import random  # Add this import
from decimal import Decimal

# Create your models here.

class Package(models.Model):
    PACKAGE_TYPES = [
        ('pro', 'Pro Package'),
        ('silver', 'Silver Package'),
    ]
    
    name = models.CharField(max_length=100)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    features = models.JSONField(default=list)
    
    # Package-specific benefits
    referral_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    daily_login_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    daily_game_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    withdrawal_priority = models.IntegerField(default=1)  # Lower number = higher priority
    
    def __str__(self):
        return f"{self.name} - ₦{self.price}"

class Coupon(models.Model):
    coupon_code = models.CharField(max_length=22, unique=True)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    price_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.coupon_code} - {self.package.name}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)
    wallet_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_submissions = models.IntegerField(default=0)
    approved_submissions = models.IntegerField(default=0)
    last_daily_login = models.DateTimeField(null=True, blank=True)
    last_daily_game = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            # Generate unique referral code: META + 4-digit number
            while True:
                code = f"META{random.randint(1000, 9999)}"
                if not UserProfile.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.package.name if self.package else 'No Package'}"

class ContentSubmission(models.Model):
    PLATFORM_CHOICES = [
        ('tiktok', 'TikTok'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    video_url = models.URLField()
    description = models.TextField(blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    review_notes = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        
        # Update user's total submissions count when new submission is created
        if is_new:
            profile = self.user.userprofile
            profile.total_submissions += 1
            profile.save()
        
        # Handle approval
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()
            # Set earnings based on platform
            platform_earnings = {
                'tiktok': Decimal('500'),
                'instagram': Decimal('400'),
                'facebook': Decimal('300'),
            }
            self.earnings = platform_earnings.get(self.platform, Decimal('200'))
            
            # Update user's approved submissions count
            profile = self.user.userprofile
            profile.approved_submissions += 1
            profile.save()
        
        # Handle payment
        if self.status == 'paid' and not self.paid_at:
            self.paid_at = timezone.now()
            # Add earnings to wallet
            if self.earnings > 0:
                profile = self.user.userprofile
                profile.wallet_balance += self.earnings
                profile.total_earnings += self.earnings
                profile.save()
                
                # Create transaction record
                Transaction.objects.create(
                    user=self.user,
                    amount=self.earnings,
                    transaction_type='content',
                    description=f'{self.get_platform_display()} video payment'
                )
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.platform}"

class Referral(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    referee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_received')
    referral_date = models.DateTimeField(auto_now_add=True)
    reward_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('referrer', 'referee')
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.reward_earned:  # New referral
            referrer_profile = self.referrer.userprofile
            if referrer_profile.package:
                self.reward_earned = referrer_profile.package.referral_bonus
                
                # Add to referrer's wallet
                referrer_profile.wallet_balance += self.reward_earned
                referrer_profile.total_earnings += self.reward_earned
                referrer_profile.save()
                
                # Create transaction
                Transaction.objects.create(
                    user=self.referrer,
                    amount=self.reward_earned,
                    transaction_type='referral',
                    description=f'Referral bonus for {self.referee.username}'
                )
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.referrer.username} → {self.referee.username}"

class GameParticipation(models.Model):
    GAME_CHOICES = [
        ('daily_spin', 'Daily Spin Wheel'),
        ('scratch_card', 'Scratch Card'),
        ('quiz', 'Daily Quiz'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game_type = models.CharField(max_length=50, choices=GAME_CHOICES)
    participation_date = models.DateTimeField(auto_now_add=True)
    reward_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    game_data = models.JSONField(default=dict)
    
    def save(self, *args, **kwargs):
        if self.reward_earned > 0 and not self._state.adding:
            # Update user's wallet
            profile = self.user.userprofile
            profile.wallet_balance += self.reward_earned
            profile.total_earnings += self.reward_earned
            profile.save()
            
            # Create transaction
            Transaction.objects.create(
                user=self.user,
                amount=self.reward_earned,
                transaction_type='game',
                description=f'{self.get_game_type_display()} reward'
            )
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.game_type}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('content', 'Content Submission'),
        ('referral', 'Referral Reward'),
        ('game', 'Game Reward'),
        ('daily_login', 'Daily Login Bonus'),
        ('payout', 'Withdrawal'),
        ('package_purchase', 'Package Purchase'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ₦{self.amount}"

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def priority(self):
        """Get withdrawal priority based on user's package"""
        if self.user.userprofile.package:
            return self.user.userprofile.package.withdrawal_priority
        return 2  # Default priority
    
    def __str__(self):
        return f"{self.user.username} - ₦{self.amount} - {self.status}"