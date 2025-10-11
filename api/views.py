from django.shortcuts import render

# Create your views here.
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
import random
from decimal import Decimal
from .authentication import create_jwt_token
import datetime

from .models import *
from .serializers import *

class PackageViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Package.objects.all()
    serializer_class = PackageSerializer

class CouponViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def validate_coupon(self, request):
        coupon_code = request.data.get('coupon_code')
        
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code, is_used=False)
            serializer = CouponSerializer(coupon)
            return Response({
                'valid': True,
                'coupon': serializer.data
            })
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid or used coupon code'
            }, status=status.HTTP_400_BAD_REQUEST)


class AuthView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Get coupon
            coupon = Coupon.objects.get(coupon_code=data['coupon_code'])
            
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            
            # Create user profile with package
            profile = UserProfile.objects.create(user=user, package=coupon.package)
            
            # Handle referral
            if data.get('referral_code'):
                try:
                    referrer_profile = UserProfile.objects.get(referral_code=data['referral_code'])
                    Referral.objects.create(
                        referrer=referrer_profile.user,
                        referee=user
                    )
                except UserProfile.DoesNotExist:
                    pass
            
            # Mark coupon as used
            coupon.is_used = True
            coupon.used_by = user
            coupon.used_at = timezone.now()
            coupon.save()
            
            # Create token
            token = create_jwt_token(user)
            
            return Response({
                'success': 'Account created successfully',
                'token': token,
                'user': UserSerializer(user).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                token = create_jwt_token(user)
                return Response({
                    'token': token,
                    'user': UserSerializer(user).data
                })
            else:
                return Response({'error': 'Invalid credentials'}, status=400)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=400)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                token = create_jwt_token(user)
                return Response({
                    'token': token,
                    'user': UserSerializer(user).data
                })
            else:
                return Response({'error': 'Invalid credentials'}, status=400)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=400)

class UserProfileViewSet(viewsets.ViewSet):
    basename = 'profile'
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def list(self, request):
        pass
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

class ContentSubmissionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ContentSubmissionSerializer
    
    def get_queryset(self):
        return ContentSubmission.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReferralViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReferralSerializer
    
    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)

class GameViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def play(self, request):
        serializer = GamePlaySerializer(data=request.data)
        if serializer.is_valid():
            game_type = serializer.validated_data['game_type']
            user = request.user
            profile = user.userprofile
            
            # Check if user already played today
            today = timezone.now().date()
            last_game = GameParticipation.objects.filter(
                user=user, 
                game_type=game_type,
                participation_date__date=today
            ).first()
            
            if last_game:
                return Response({
                    'error': f'You have already played {game_type} today'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate reward based on package
            if profile.package:
                base_reward = profile.package.daily_game_bonus
            else:
                base_reward = Decimal('100')  # Default reward
            
            # Add some randomness
            reward_variation = random.uniform(0.5, 1.5)
            reward = round(base_reward * Decimal(reward_variation), 2)
            
            # Create game participation
            game = GameParticipation.objects.create(
                user=user,
                game_type=game_type,
                reward_earned=reward,
                game_data={'base_reward': float(base_reward), 'multiplier': reward_variation}
            )
            
            # Update last game date
            profile.last_daily_game = timezone.now()
            profile.save()
            
            return Response({
                'success': f'You won ₦{reward}!',
                'reward': float(reward),
                'game_id': game.id
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DailyLoginView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        profile = user.userprofile
        
        # Check if user already claimed today
        today = timezone.now().date()
        if profile.last_daily_login and profile.last_daily_login.date() == today:
            return Response({
                'error': 'Daily login bonus already claimed today'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate bonus based on package
        if profile.package:
            bonus = profile.package.daily_login_bonus
        else:
            bonus = Decimal('50')  # Default bonus
        
        # Add bonus to wallet
        profile.wallet_balance += bonus
        profile.total_earnings += bonus
        profile.last_daily_login = timezone.now()
        profile.save()
        
        # Create transaction
        Transaction.objects.create(
            user=user,
            amount=bonus,
            transaction_type='daily_login',
            description='Daily login bonus'
        )
        
        return Response({
            'success': f'₦{bonus} daily login bonus added to your wallet',
            'bonus': float(bonus)
        })

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        profile = user.userprofile
        
        # Calculate earnings from different sources
        content_earnings = ContentSubmission.objects.filter(
            user=user, 
            status='approved'
        ).aggregate(total=Sum('earnings'))['total'] or 0
        
        referral_earnings = Referral.objects.filter(
            referrer=user
        ).aggregate(total=Sum('reward_earned'))['total'] or 0
        
        game_earnings = GameParticipation.objects.filter(
            user=user
        ).aggregate(total=Sum('reward_earned'))['total'] or 0
        
        daily_login_earnings = Transaction.objects.filter(
            user=user,
            transaction_type='daily_login'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Recent activity
        recent_transactions = Transaction.objects.filter(
            user=user
        ).order_by('-date')[:10]
        
        recent_submissions = ContentSubmission.objects.filter(
            user=user
        ).order_by('-submission_date')[:5]
        
        return Response({
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data,
            'earnings_breakdown': {
                'content': float(content_earnings),
                'referrals': float(referral_earnings),
                'games': float(game_earnings),
                'daily_login': float(daily_login_earnings),
                'total': float(profile.total_earnings)
            },
            'wallet_balance': float(profile.wallet_balance),
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'recent_submissions': ContentSubmissionSerializer(recent_submissions, many=True).data,
            'referral_stats': {
                'total_referrals': Referral.objects.filter(referrer=user).count(),
                'total_earned': float(referral_earnings)
            }
        })

class WithdrawalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalRequestSerializer
    
    def get_queryset(self):
        return WithdrawalRequest.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        user = self.request.user
        profile = user.userprofile
        amount = serializer.validated_data['amount']
        
        # Check if user has sufficient balance
        if amount > profile.wallet_balance:
            raise serializers.ValidationError("Insufficient balance")
        
        # Check minimum withdrawal
        if amount < Decimal('1000'):
            raise serializers.ValidationError("Minimum withdrawal is ₦1000")
        
        # Deduct from wallet
        profile.wallet_balance -= amount
        profile.save()
        
        # Create withdrawal request
        withdrawal = serializer.save(user=user)
        
        # Create transaction
        Transaction.objects.create(
            user=user,
            amount=-amount,
            transaction_type='payout',
            description=f'Withdrawal to {withdrawal.bank_name}'
        )
        
        return withdrawal

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date')