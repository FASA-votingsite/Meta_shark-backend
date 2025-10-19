from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
import random
from .models import *
from .serializers import *
from django.db.models import Sum
from datetime import timedelta


# JWT Token generation helper
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# Authentication Views
class AuthView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print("📝 Registration request received:", request.data)
        
        serializer = SignupSerializer(data=request.data)
        
        if not serializer.is_valid():
            print("❌ Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        print("✅ Serializer is valid")
        
        try:
            with transaction.atomic():
                data = serializer.validated_data
                
                # Create user
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password']
                )
                print(f"✅ User created: {user.username}")
                
                # Get coupon and package
                coupon = data['coupon']
                package = coupon.package
                
                # Create user profile with package
                profile = UserProfile.objects.create(
                    user=user,
                    package=package,
                    phone_number=data.get('phone_number', ''),
                )
                print(f"✅ Profile created for: {user.username} with package: {package.name}")
                
                # Mark coupon as used
                coupon.is_used = True
                coupon.used_by = user
                coupon.used_at = timezone.now()
                coupon.save()
                print(f"✅ Coupon marked as used: {coupon.coupon_code}")
                
                # Handle referral if provided
                if data.get('referrer'):
                    referrer = data['referrer']
                    
                    # Fixed referral bonuses based on referee's package
                    if package.package_type == 'pro':
                        referral_bonus = Decimal('4000.00')  # ₦4000 for Pro referral
                    elif package.package_type == 'silver':
                        referral_bonus = Decimal('3000.00')  # ₦3000 for Silver referral
                    else:
                        referral_bonus = Decimal('2000.00')  # Default for other packages
                    
                    # Create referral record
                    referral = Referral.objects.create(
                        referrer=referrer,
                        referee=user,
                        reward_earned=referral_bonus,
                        referee_package=package.package_type
                    )
                    
                    # Add referral bonus to referrer's wallet
                    referrer_profile = referrer.userprofile
                    referrer_profile.wallet_balance += referral_bonus
                    referrer_profile.total_earnings += referral_bonus
                    referrer_profile.save()
                    
                    # Create transaction for referrer
                    Transaction.objects.create(
                        user=referrer,
                        amount=referral_bonus,
                        transaction_type='referral',
                        description=f'Referral bonus for {user.username} ({package.package_type.title()} package)'
                    )
                    
                    print(f"✅ Referral created for: {referrer.username} with bonus: ₦{referral_bonus}")
                
                # Generate JWT tokens
                tokens = get_tokens_for_user(user)
                print(f"✅ JWT tokens generated for: {user.username}")
                
                # Prepare user data for response
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': profile.phone_number,
                    'wallet_balance': float(profile.wallet_balance),
                    'total_earnings': float(profile.total_earnings),
                    'referral_code': profile.referral_code,
                    'package': {
                        'id': package.id,
                        'name': package.name,
                        'type': package.package_type,
                        'price': float(package.price),
                    } if package else None
                }
                
                return Response({
                    'token': tokens['access'],
                    'refresh': tokens['refresh'],
                    'user': user_data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            print(f"❌ Error during registration: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Registration failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Login View with JWT
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print("🔐 Login request received:", request.data)
        
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        phone_number = serializer.validated_data.get('phone_number', '')
        whatsapp_number = serializer.validated_data.get('whatsapp_number', '')  # Added whatsapp_number
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Update phone number or whatsapp number if provided
            if phone_number or whatsapp_number:
                try:
                    profile = user.userprofile
                    if phone_number:
                        profile.phone_number = phone_number
                    if whatsapp_number:
                        profile.whatsapp_number = whatsapp_number
                    profile.save()
                except UserProfile.DoesNotExist:
                    UserProfile.objects.create(
                        user=user, 
                        phone_number=phone_number,
                        whatsapp_number=whatsapp_number
                    )
            
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            # Prepare user data
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': profile.phone_number,
                'whatsapp_number': profile.whatsapp_number,
                'wallet_balance': float(profile.wallet_balance),
                'total_earnings': float(profile.total_earnings),
                'referral_code': profile.referral_code,
                'package': {
                    'id': profile.package.id if profile.package else None,
                    'name': profile.package.name if profile.package else None,
                    'type': profile.package.package_type if profile.package else None,
                    'price': float(profile.package.price) if profile.package else 0,
                } if profile.package else None
            }
            
            print(f"✅ Login successful for: {user.username}")
            return Response({
                'token': tokens['access'],
                'refresh': tokens['refresh'],
                'user': user_data
            })
        else:
            print("❌ Login failed: Invalid credentials")
            return Response({
                'error': 'Invalid username or password'
            }, status=status.HTTP_400_BAD_REQUEST)

# Token Refresh View
class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            data = {
                'access': str(refresh.access_token),
            }
            return Response(data)
        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
        
class ValidateCouponView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        coupon_code = request.data.get('coupon_code')
        
        print(f"🎫 Coupon validation request: {coupon_code}")
        
        if not coupon_code:
            print("❌ No coupon code provided")
            return Response(
                {"error": "Coupon code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code, is_used=False)
            print(f"✅ Valid coupon found: {coupon.coupon_code} for {coupon.package.name}")
            return Response({
                'valid': True,
                'package': {
                    'id': coupon.package.id,
                    'name': coupon.package.name,
                    'price': float(coupon.package.price)
                }
            })
        except Coupon.DoesNotExist:
            print(f"❌ Invalid or used coupon: {coupon_code}")
            return Response({
                'valid': False,
                'error': 'Invalid or used coupon code'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"❌ Coupon validation error: {str(e)}")
            return Response({
                'valid': False,
                'error': 'Server error during coupon validation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """Verify that the token is valid"""
    return Response({
        'valid': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email
        }
    })

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.userprofile
            submissions = ContentSubmission.objects.filter(user=request.user)
            referrals = Referral.objects.filter(referrer=request.user)
            transactions = Transaction.objects.filter(user=request.user)
            
            # Import serializers here to avoid circular imports
            from .serializers import (
                PackageSerializer, TransactionSerializer, 
                ContentSubmissionSerializer
            )
            
            # Calculate platform-specific earnings from APPROVED/PAID submissions
            platform_earnings = {
                'tiktok': Decimal('0'),
                'instagram': Decimal('0'),
                'facebook': Decimal('0')
            }
            
            approved_submissions = submissions.filter(status__in=['approved', 'paid'])
            for submission in approved_submissions:
                platform = submission.platform.lower()
                if platform in platform_earnings:
                    platform_earnings[platform] += submission.earnings
            
            # Calculate total content earnings (sum of all platforms)
            total_content_earnings = sum(platform_earnings.values())
            
            # Calculate earnings breakdown from transactions (only positive amounts)
            earnings_breakdown = {
                'content': total_content_earnings,  # Use actual content earnings
                'referrals': Decimal('0'),
                'games': Decimal('0'),
                'daily_login': Decimal('0')
            }
            
            for transaction in transactions.filter(amount__gt=0):
                if transaction.transaction_type in earnings_breakdown:
                    earnings_breakdown[transaction.transaction_type] += transaction.amount
            
            # Verify that total_earnings matches the sum of all earnings
            calculated_total_earnings = (
                earnings_breakdown['content'] +
                earnings_breakdown['referrals'] +
                earnings_breakdown['games'] +
                earnings_breakdown['daily_login']
            )
            
            # If there's a discrepancy, use the calculated total
            if profile.total_earnings != calculated_total_earnings:
                print(f"⚠️ Total earnings mismatch: Profile={profile.total_earnings}, Calculated={calculated_total_earnings}")
                # You might want to sync this in production
            
            recent_submissions = submissions.order_by('-submission_date')[:10]
            
            data = {
                'wallet_balance': float(profile.wallet_balance),
                'total_earnings': float(profile.total_earnings),
                'total_balance': float(profile.total_earnings),  # Use profile total_earnings
                'package': PackageSerializer(profile.package).data if profile.package else None,
                'submission_count': submissions.count(),
                'referral_count': referrals.count(),
                'recent_transactions': TransactionSerializer(
                    transactions.order_by('-date')[:5],
                    many=True
                ).data,
                'recent_submissions': ContentSubmissionSerializer(
                    recent_submissions, many=True
                ).data,
                'referral_stats': {
                    'total_referrals': referrals.count(),
                    'total_earned': float(sum([r.reward_earned for r in referrals]))
                },
                'earnings_breakdown': {
                    'content': float(earnings_breakdown['content']),
                    'referrals': float(earnings_breakdown['referrals']),
                    'games': float(earnings_breakdown['games']),
                    'daily_login': float(earnings_breakdown['daily_login'])
                },
                'platform_stats': {
                    'tiktok': {
                        'earnings': float(platform_earnings['tiktok']),
                        'submissions': submissions.filter(platform='tiktok').count(),
                        'approved': submissions.filter(platform='tiktok', status__in=['approved', 'paid']).count()
                    },
                    'instagram': {
                        'earnings': float(platform_earnings['instagram']),
                        'submissions': submissions.filter(platform='instagram').count(),
                        'approved': submissions.filter(platform='instagram', status__in=['approved', 'paid']).count()
                    },
                    'facebook': {
                        'earnings': float(platform_earnings['facebook']),
                        'submissions': submissions.filter(platform='facebook').count(),
                        'approved': submissions.filter(platform='facebook', status__in=['approved', 'paid']).count()
                    }
                }
            }
            return Response(data)
        except Exception as e:
            print(f"❌ Dashboard error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Failed to load dashboard data: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
                    
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
        
        # Calculate base bonus based on package - FIXED AMOUNTS
        if profile.package:
            if profile.package.package_type == 'pro':
                base_bonus = Decimal('1000.00')  # Pro package gets exactly ₦1000
            elif profile.package.package_type == 'silver':
                base_bonus = Decimal('700.00')   # Silver package gets exactly ₦700
            else:
                base_bonus = Decimal('500.00')   # Default for any other package
        else:
            base_bonus = Decimal('500.00')  # Default bonus for no package
        
        # Calculate streak
        yesterday = today - timedelta(days=1)
        current_streak = 1
        
        if profile.last_daily_login:
            last_login_date = profile.last_daily_login.date()
            if last_login_date == yesterday:
                # Consecutive login - increment streak
                current_streak = getattr(profile, 'login_streak', 0) + 1
            elif last_login_date == today:
                # Already claimed today
                return Response({
                    'error': 'Daily login bonus already claimed today'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # NO streak bonus multiplier - use exact base amounts
        final_bonus = base_bonus  # Remove streak multiplier
        
        # Update user profile - add to BOTH wallet_balance AND total_earnings
        profile.wallet_balance += final_bonus
        profile.total_earnings += final_bonus
        profile.last_daily_login = timezone.now()
        profile.login_streak = current_streak
        profile.save()
        
        # Create transaction
        Transaction.objects.create(
            user=user,
            amount=final_bonus,
            transaction_type='daily_login',
            description=f'Daily login bonus - {profile.package.name if profile.package else "Basic"}'
        )
        
        # Create game participation record
        game = GameParticipation.objects.create(
            user=user,
            game_type='daily_login',
            reward_earned=final_bonus,
            game_data={
                'type': 'daily_login', 
                'base_bonus': float(base_bonus),
                'final_bonus': float(final_bonus),
                'streak_count': current_streak,
                'package_type': profile.package.package_type if profile.package else 'none'
            }
        )
        
        return Response({
            'success': True,
            'bonus_amount': float(final_bonus),
            'base_bonus': float(base_bonus),
            'streak_count': current_streak,
            'package_type': profile.package.package_type if profile.package else 'none',
            'message': f'₦{final_bonus} daily login bonus added to your wallet!',
            'game_id': game.id
        })
    
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
    permission_classes = [IsAuthenticated]
    serializer_class = ContentSubmissionSerializer
    queryset = ContentSubmission.objects.all()
    
    def get_queryset(self):
        return ContentSubmission.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        try:
            # Save the submission with the current user
            submission = serializer.save(user=self.request.user)
            
            # Set initial status and earnings
            submission.status = 'pending'
            submission.earnings = 0
            submission.save()
            
            return submission
        except Exception as e:
            print(f"Error creating submission: {e}")
            raise
    
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return response
        except Exception as e:
            return Response(
                {'error': 'Failed to submit content. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ReferralViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReferralSerializer
    
    def get_queryset(self):
        return Referral.objects.filter(referrer=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user
        referrals = Referral.objects.filter(referrer=user)
        
        total_referrals = referrals.count()
        total_earned = referrals.aggregate(total=Sum('reward_earned'))['total'] or 0
        pending_earnings = referrals.filter(is_paid=False).aggregate(total=Sum('reward_earned'))['total'] or 0
        
        return Response({
            'total_referrals': total_referrals,
            'total_earned': float(total_earned),
            'pending_earnings': float(pending_earnings)
        })
    
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"❌ Profile fetch error: {str(e)}")
            return Response({"error": "Failed to fetch profile"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class WalletView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile = request.user.userprofile
        return Response({
            'balance': float(profile.wallet_balance),
            'total_earnings': float(profile.total_earnings)
        })

class WithdrawalViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalRequestSerializer
    
    def get_queryset(self):
        return WithdrawalRequest.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        try:
            user = request.user
            password = request.data.get('password')
            amount = Decimal(request.data.get('amount', 0))
            
            print(f"🔍 Withdrawal request data: {request.data}")
            
            # Verify password
            if not password:
                return Response(
                    {"error": "Password is required to process withdrawal"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not user.check_password(password):
                return Response(
                    {"error": "Invalid password"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user has sufficient balance
            profile = user.userprofile
            if amount > profile.wallet_balance:
                return Response(
                    {"error": f"Insufficient balance. Available: ₦{profile.wallet_balance}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if amount < Decimal('1000'):
                return Response(
                    {"error": "Minimum withdrawal amount is ₦1,000"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate other required fields
            required_fields = ['bank_name', 'account_number', 'account_name']
            for field in required_fields:
                if not request.data.get(field):
                    return Response(
                        {"error": f"{field.replace('_', ' ').title()} is required"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create withdrawal request
            withdrawal_data = {
                'amount': amount,
                'bank_name': request.data.get('bank_name'),
                'account_number': request.data.get('account_number'),
                'account_name': request.data.get('account_name'),
                'user': user
            }
            
            serializer = self.get_serializer(data=withdrawal_data)
            serializer.is_valid(raise_exception=True)
            
            # Deduct amount from wallet
            profile.wallet_balance -= amount
            profile.save()
            
            # Create transaction record
            Transaction.objects.create(
                user=user,
                amount=-amount,  # Negative amount for withdrawal
                transaction_type='payout',
                description=f'Withdrawal to {request.data.get("bank_name")} - {request.data.get("account_number")}'
            )
            
            withdrawal = serializer.save()
            
            return Response({
                'success': True,
                'message': f'Withdrawal request of ₦{amount} submitted successfully',
                'withdrawal_id': withdrawal.id,
                'new_balance': float(profile.wallet_balance)
            }, status=status.HTTP_201_CREATED)
            
        except serializers.ValidationError as e:
            print(f"❌ Withdrawal validation error: {e.detail}")
            return Response(
                {"error": f"Validation error: {e.detail}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(f"❌ Withdrawal error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Withdrawal failed: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

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
        profile = user.userprofile
        
        if not game_type:
            return Response({'error': 'Game type is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already played this game today
        today = timezone.now().date()
        last_game = GameParticipation.objects.filter(
            user=user, 
            game_type=game_type,
            participation_date__date=today
        ).first()
        
        if last_game:
            return Response({
                'error': f'You have already played {self.get_game_name(game_type)} today'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate reward based on game type and package
        base_rewards = {
            'daily_spin': Decimal('500'),
            'scratch_card': Decimal('300'),
            'quiz': Decimal('200')
        }
        
        base_reward = base_rewards.get(game_type, Decimal('100'))
        
        # Apply package multiplier
        if profile.package:
            if profile.package.package_type == 'pro':
                base_reward *= Decimal('1.5')  # 50% more for pro
            elif profile.package.package_type == 'silver':
                base_reward *= Decimal('1.2')  # 20% more for silver
        
        # Add some randomness
        reward_variation = random.uniform(0.8, 1.5)
        reward = round(base_reward * Decimal(reward_variation), 2)
        
        # Create game participation
        game = GameParticipation.objects.create(
            user=user,
            game_type=game_type,
            reward_earned=reward,
            game_data={
                'base_reward': float(base_reward), 
                'multiplier': reward_variation,
                'game_type': game_type
            }
        )
        
        # Update user wallet
        profile.wallet_balance += reward
        profile.total_earnings += reward
        profile.last_daily_game = timezone.now()
        profile.save()
        
        # Create transaction
        Transaction.objects.create(
            user=user,
            amount=reward,
            transaction_type='game',
            description=f'{self.get_game_name(game_type)} reward'
        )
        
        return Response({
            'success': True,
            'reward': float(reward),
            'message': f'You won ₦{reward} from {self.get_game_name(game_type)}!',
            'game_id': game.id
        })
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        games = GameParticipation.objects.filter(user=request.user).order_by('-participation_date')[:20]
        serializer = GameParticipationSerializer(games, many=True)
        return Response(serializer.data)
    
    def get_game_name(self, game_type):
        names = {
            'daily_spin': 'Daily Spin',
            'scratch_card': 'Scratch Card',
            'quiz': 'Daily Quiz',
            'daily_login': 'Daily Login'
        }
        return names.get(game_type, game_type)
    

class GameHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get game participation history for the user
            games = GameParticipation.objects.filter(user=request.user).order_by('-participation_date')[:20]
            from .serializers import GameParticipationSerializer
            serializer = GameParticipationSerializer(games, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(f"❌ Game history error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Failed to fetch game history: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )