from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '_all_'

class CouponSerializer(serializers.ModelSerializer):
    package = PackageSerializer(read_only=True)
    
    class Meta:
        model = Coupon
        fields = '_all_'

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    package = PackageSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '_all_'

class ContentSubmissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ContentSubmission
        fields = '_all_'
        read_only_fields = ('user', 'submission_date', 'earnings')

class ReferralSerializer(serializers.ModelSerializer):
    referrer = UserSerializer(read_only=True)
    referee = UserSerializer(read_only=True)
    
    class Meta:
        model = Referral
        fields = '_all_'

class GameParticipationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = GameParticipation
        fields = '_all_'
        read_only_fields = ('user', 'participation_date')

class TransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = '_all_'
        read_only_fields = ('user', 'date')

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    priority = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = '_all_'
        read_only_fields = ('user', 'status', 'created_at', 'processed_at')

class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    coupon_code = serializers.CharField()
    referral_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("Username already exists")
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists")
        
        # Validate coupon
        try:
            coupon = Coupon.objects.get(coupon_code=data['coupon_code'], is_used=False)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid or used coupon code")
        
        return data

class DailyLoginSerializer(serializers.Serializer):
    pass

class GamePlaySerializer(serializers.Serializer):
    game_type = serializers.ChoiceField(choices=GameParticipation.GAME_CHOICES)