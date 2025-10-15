from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from .models import *
from .serializers import *

# Authentication Views
class AuthView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            # Create user
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            
            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                phone_number=serializer.validated_data.get('phone_number', '')
            )
            
            # Mark coupon as used
            coupon = serializer.validated_data['coupon']
            coupon.is_used = True
            coupon.used_by = user
            coupon.save()
            
            # Assign package to user
            profile.package = coupon.package
            profile.save()
            
            # Create token
            token = Token.objects.create(user=user)
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {"error": "Please provide both username and password"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if user:
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            
            # Get user profile
            try:
                profile = UserProfile.objects.get(user=user)
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'package': profile.package.name if profile.package else None,
                    'wallet_balance': float(profile.wallet_balance),
                    'phone_number': profile.phone_number
                }
            except UserProfile.DoesNotExist:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            
            return Response({
                'token': token.key,
                'user': user_data
            })
        else:
            return Response(
                {"error": "Invalid username or password"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class ValidateCouponView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        coupon_code = request.data.get('coupon_code')
        
        if not coupon_code:
            return Response(
                {"error": "Coupon code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code, is_used=False)
            return Response({
                'valid': True,
                'package': {
                    'id': coupon.package.id,
                    'name': coupon.package.name,
                    'price': float(coupon.package.price)
                }
            })
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid or used coupon code'
            }, status=status.HTTP_400_BAD_REQUEST)

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        submissions = ContentSubmission.objects.filter(user=request.user)
        referrals = Referral.objects.filter(referrer=request.user)
        
        data = {
            'wallet_balance': float(profile.wallet_balance),
            'total_earnings': float(profile.total_earnings),
            'package': PackageSerializer(profile.package).data if profile.package else None,
            'submission_count': submissions.count(),
            'referral_count': referrals.count(),
        }
        return Response(data)

class DailyLoginView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        profile = UserProfile.objects.get(user=request.user)
        
        # Check if user already claimed daily login today
        today = timezone.now().date()
        if profile.last_daily_login and profile.last_daily_login.date() == today:
            return Response({
                'error': 'Daily login bonus already claimed today'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add daily login bonus
        if profile.package:
            bonus_amount = profile.package.daily_login_bonus
            profile.wallet_balance += bonus_amount
            profile.total_earnings += bonus_amount
            profile.last_daily_login = timezone.now()
            profile.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=request.user,
                amount=bonus_amount,
                transaction_type='daily_login',
                description='Daily login bonus'
            )
            
            return Response({
                'success': True,
                'bonus_amount': float(bonus_amount),
                'new_balance': float(profile.wallet_balance)
            })
        
        return Response({
            'error': 'No package assigned to user'
        }, status=status.HTTP_400_BAD_REQUEST)

# ViewSets
class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def validate(self, request):
        coupon_code = request.data.get('coupon_code')
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code, is_used=False)
            return Response({
                'valid': True,
                'package': PackageSerializer(coupon.package).data
            })
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid or used coupon code'
            }, status=status.HTTP_400_BAD_REQUEST)

class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [AllowAny]

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ContentSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = ContentSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ContentSubmission.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReferralViewSet(viewsets.ModelViewSet):
    serializer_class = ReferralSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)

class WithdrawalViewSet(viewsets.ModelViewSet):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

class GameParticipationViewSet(viewsets.ModelViewSet):
    serializer_class = GameParticipationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GameParticipation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class GameViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def play(self, request):
        game_type = request.data.get('game_type')
        user = request.user
        profile = UserProfile.objects.get(user=user)
        
        # Check if user can play game today
        today = timezone.now().date()
        if profile.last_daily_game and profile.last_daily_game.date() == today:
            return Response({
                'error': 'You have already played a game today'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate reward based on package
        if profile.package:
            reward_amount = profile.package.daily_game_bonus
            
            # Update user profile
            profile.wallet_balance += reward_amount
            profile.total_earnings += reward_amount
            profile.last_daily_game = timezone.now()
            profile.save()
            
            # Create game participation record
            game_participation = GameParticipation.objects.create(
                user=user,
                game_type=game_type,
                reward_earned=reward_amount
            )
            
            # Create transaction record
            Transaction.objects.create(
                user=user,
                amount=reward_amount,
                transaction_type='game',
                description=f'{game_type} game reward'
            )
            
            return Response({
                'success': True,
                'reward': float(reward_amount),
                'new_balance': float(profile.wallet_balance),
                'game_type': game_type
            })
        
        return Response({
            'error': 'No package assigned to user'
        }, status=status.HTTP_400_BAD_REQUEST)