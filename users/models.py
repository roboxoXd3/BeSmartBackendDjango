from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    
    # Add other fields if necessary from Supabase auth.users if we want to migrate them directly
    # For now, standard Django User with UUID + Email as username is good practice
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Profile(models.Model):
    id = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile', db_column='id')
    full_name = models.TextField(null=True, blank=True)
    phone_number = models.TextField(null=True, blank=True)
    image_path = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Role enum handled as string/choice in Django usually
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'profiles'  # Map to existing table if we want, but 'public.profiles' might conflict if we let Django manage it.
        # If we want to strictly map to existing 'public.profiles', we can use managed = False
        # But we are migrating away, so managed = True is fine, assuming we handle the data migration.
