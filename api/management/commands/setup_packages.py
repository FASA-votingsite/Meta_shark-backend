from django.core.management.base import BaseCommand
from api.models import Package

class Command(BaseCommand):
    help = 'Create initial META_SHARK packages'
    
    def handle(self, *args, **options):
        # Pro Package
        pro_package, created = Package.objects.get_or_create(
            package_type='pro',
            defaults={
                'name': 'Pro Package',
                'price': 10000,
                'description': 'Premium package with automatic features and highest earnings',
                'features': [
                    'Auto claim reward',
                    'Earn ₦4,000 per referred user',
                    '₦1,000 daily login bonus',
                    'Fast withdrawal processing',
                    'Priority support',
                    'Advanced analytics'
                ],
                'referral_bonus': 4000,
                'daily_login_bonus': 1000,
                'daily_game_bonus': 700,
                'withdrawal_priority': 1
            }
        )
        
        # Silver Package
        silver_package, created = Package.objects.get_or_create(
            package_type='silver',
            defaults={
                'name': 'Silver Package',
                'price': 8000,
                'description': 'Standard package with manual features and good earnings',
                'features': [
                    'Manual features',
                    'Earn ₦3,000 per referred user',
                    '₦700 daily game bonus',
                    'Standard withdrawal processing',
                    'Basic support'
                ],
                'referral_bonus': 3000,
                'daily_login_bonus': 0,
                'daily_game_bonus': 700,
                'withdrawal_priority': 2
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created META_SHARK packages')
        )