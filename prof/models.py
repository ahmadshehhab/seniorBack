import uuid
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
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

class UsersCategory(models.Model):
    type = models.CharField(max_length=255 , null=False , blank=False)
    def __str__(self):
        return self.type
class CityCategory(models.Model):
    city = models.CharField(max_length=255 , null=False , blank=False)
    def __str__(self):
        return self.city
class PostsCategory(models.Model):
    category = models.CharField(max_length=255 , null=False , blank=False)
    def __str__(self):
        return self.category

class Posts(models.Model):
    status_choices = [
        (True, 'Active'),
        (False, 'Inactive'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='job_images/', blank=True, null=True)
    homeowner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    post_date = models.DateField(null=True, blank=True)
    post_time = models.TimeField(null=True, blank=True)
    is_accepted = models.IntegerField(null=True, blank=True)
    category = models.ForeignKey(PostsCategory, on_delete=models.CASCADE, related_name='post_category',null=False , blank=False,  default=1)
    price = models.CharField(null=False , blank=False , default="الاتفاق عبر الهاتف" , max_length=255)
    status = models.BooleanField(
        choices=status_choices,
        default=False,
        null=False,
        blank=False
    )
    scheduled_datetime = models.DateTimeField(
        null=True, blank=True)  # Combines post_date + post_time

    def save(self, *args, **kwargs):

        if self.post_date and self.post_time:
            self.scheduled_datetime = datetime.combine(self.post_date, self.post_time)
        super().save(*args, **kwargs)
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
