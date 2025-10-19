from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        # REMOVED "phone_number" from here since User model doesn't have it

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'

class CouponSerializer(serializers.ModelSerializer):
    package = PackageSerializer(read_only=True)
    
    class Meta:
        model = Coupon
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    package = PackageSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'package', 'referral_code', 'referred_by', 'phone_number',
            'whatsapp_number', 'wallet_balance', 'total_earnings', 
            'total_submissions', 'approved_submissions', 'last_daily_login',
            'last_daily_game', 'login_streak'  
        ]
        read_only_fields = ['referral_code', 'wallet_balance', 'total_earnings']

class ContentSubmissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ContentSubmission
        fields = [
            'id', 'user', 'platform', 'platform_display', 'video_url', 'description',
            'submission_date', 'status', 'status_display', 'earnings',
            'review_notes', 'approved_at', 'paid_at'
        ]
        read_only_fields = ['user', 'submission_date', 'status', 'earnings', 'approved_at', 'paid_at']

class ReferralSerializer(serializers.ModelSerializer):
    referrer = UserSerializer(read_only=True)
    referee = UserSerializer(read_only=True)
    
    class Meta:
        model = Referral
        fields = '__all__'

class GameParticipationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = GameParticipation
        fields = '__all__'
        read_only_fields = ('user', 'participation_date')

class TransactionSerializer(serializers.ModelSerializer):
    # Use a simpler user representation to avoid errors
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'user_username', 'user_email', 'amount', 'transaction_type', 'description', 'date']
        read_only_fields = ['user_username', 'user_email', 'date']

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    priority = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = '__all__'
        read_only_fields = ('user', 'status', 'created_at', 'processed_at')

class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    coupon_code = serializers.CharField()
    referral_code = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=True, allow_blank=False, max_length=14)
    
    def validate(self, data):
        print("🔍 Validating registration data:", data)
        
        # Password validation
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        # Username validation
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already exists")
        
        # Email validation
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists")
        
        # Coupon validation
        try:
            coupon = Coupon.objects.get(coupon_code=data['coupon_code'], is_used=False)
            data['coupon'] = coupon
            print(f"✅ Coupon validated: {coupon.coupon_code}")
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid or used coupon code")
        
        # Referral code validation (if provided)
        if data.get('referral_code'):
            try:
                referrer_profile = UserProfile.objects.get(referral_code=data['referral_code'])
                data['referrer'] = referrer_profile.user
                print(f"✅ Referral code validated: {data['referral_code']}")
            except UserProfile.DoesNotExist:
                raise serializers.ValidationError("Invalid referral code")
        
        return data
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    phone_number = serializers.CharField(required=False, allow_blank=True)
    whatsapp_number = serializers.CharField(required=False, allow_blank=True)  # Add this
    
class DailyLoginSerializer(serializers.Serializer):
    pass

class GamePlaySerializer(serializers.Serializer):
    game_type = serializers.ChoiceField(choices=GameParticipation.GAME_CHOICES)

class CouponValidationSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=22)
    
    def validate_coupon_code(self, value):
        """Validate coupon code format and existence"""
        value = value.strip().lower()
        
        # Check if coupon exists and is not used
        try:
            coupon = Coupon.objects.get(coupon_code=value, is_used=False)
            return value
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid or used coupon code")

class WithdrawalRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = ('amount', 'bank_name', 'account_number', 'account_name')
    
    def validate_amount(self, value):
        """Validate withdrawal amount"""
        if value <= 0:
            raise serializers.ValidationError("Withdrawal amount must be greater than 0")
        
        # In practice, you'd check if user has sufficient balance
        # This would be done in the view
        return value

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
    confirm_new_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match")
        return data

class ProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    
    class Meta:
        model = UserProfile
        fields = ('phone_number', 'email', 'first_name', 'last_name')
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        # Update user fields
        user = instance.user
        if 'email' in user_data:
            user.email = user_data['email']
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        user.save()
        
        # Update profile fields
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()
        
        return instance