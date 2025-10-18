from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'packages', views.PackageViewSet)
router.register(r'coupons', views.CouponViewSet)
router.register(r'user-profiles', views.UserProfileViewSet, basename='userprofile')  # Changed from 'profile'
router.register(r'content', views.ContentSubmissionViewSet, basename='content')
router.register(r'referrals', views.ReferralViewSet, basename='referral')
router.register(r'withdrawals', views.WithdrawalViewSet, basename='withdrawal')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'game-participations', views.GameParticipationViewSet, basename='gameparticipation')

urlpatterns = [
    # Authentication endpoints
    path('api/auth/register/', views.AuthView.as_view(), name='register'),
    path('api/auth/login/', views.LoginView.as_view(), name='login'),
    path('api/auth/validate-coupon/', views.ValidateCouponView.as_view(), name='validate-coupon'),
    path('api/auth/verify-token/', views.verify_token, name='verify-token'),
    path('api/auth/token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    
    # Dashboard & User endpoints
    path('api/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('api/profile/', views.ProfileView.as_view(), name='profile'),  # This is the APIView
    path('api/wallet/balance/', views.WalletView.as_view(), name='wallet-balance'),
    
    # Daily Login endpoint
    path('api/daily-login/', views.DailyLoginView.as_view(), name='daily-login'),
    
    # Games endpoints
    path('api/games/play/', views.GameViewSet.as_view({'post': 'play'}), name='play-game'),
    path('api/games/history/', views.GameHistoryView.as_view(), name='game-history'),
    
    # Include router URLs last
    path('api/', include(router.urls)),
]