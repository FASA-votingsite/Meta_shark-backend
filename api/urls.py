from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'packages', views.PackageViewSet, basename='package')
router.register(r'coupons', views.CouponViewSet, basename='coupon')
router.register(r'profile', views.UserProfileViewSet, basename='profile')
router.register(r'content', views.ContentSubmissionViewSet, basename='content')
router.register(r'referrals', views.ReferralViewSet, basename='referral')
router.register(r'withdrawals', views.WithdrawalViewSet, basename='withdrawal')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/signup/', views.AuthView.as_view(), name='signup'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('games/play/', views.GameViewSet.as_view({'post': 'play'}), name='game-play'),
    path('daily-login/', views.DailyLoginView.as_view(), name='daily-login'),
]