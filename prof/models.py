import uuid
from django.db import models
from django.contrib.auth.models import User
class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('homeowner', 'Homeowner'),
        ('worker', 'Worker'),
        ('company', 'Company'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    companyId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_users',null=True , blank=True)
    workAs = models.CharField(max_length=255 , null=True , blank=True)
    phone = models.CharField(max_length=15, blank=False, null=False , default="0")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='homeowner'
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_user_type_display()})"

    @staticmethod
    def create_profile_for_user(user):
        """Create a default user profile."""
        UserProfile.objects.get_or_create(user=user, phone="0", user_type='homeowner')


        
class Posts(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='job_images/', blank=True, null=True)
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title




class WorkerInvitation(models.Model):
    email = models.EmailField()
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations')
    is_accepted = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('email', 'company')  # Prevent multiple invitations for the same user
