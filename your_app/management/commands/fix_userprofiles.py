from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from your_app.models import UserProfile

class Command(BaseCommand):
    help = 'Fix UserProfile issues by creating missing profiles'
    
    def handle(self, *args, **options):
        # Create UserProfile for any users that don't have one
        users_without_profiles = User.objects.filter(userprofile__isnull=True)
        
        for user in users_without_profiles:
            UserProfile.objects.create(user=user)
            self.stdout.write(
                self.style.SUCCESS(f'Created UserProfile for {user.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully fixed all UserProfile issues')
        )