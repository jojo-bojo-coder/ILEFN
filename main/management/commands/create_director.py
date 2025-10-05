from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import DirectorProfile


class Command(BaseCommand):
    help = 'Create a director user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Director username')
        parser.add_argument('--password', type=str, help='Director password')
        parser.add_argument('--email', type=str, help='Director email')

    def handle(self, *args, **options):
        username = options['username'] or 'nagham'
        password = options['password'] or '123'
        email = options['email'] or 'naghamzanaty7@gmail.com'

        # Create user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': False
            }
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'User {username} created successfully')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'User {username} already exists')
            )

        # Create director profile
        director_profile, created = DirectorProfile.objects.get_or_create(user=user)
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Director profile created for {username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Director profile already exists for {username}')
            )