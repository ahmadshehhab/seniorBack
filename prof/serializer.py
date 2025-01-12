from rest_framework import serializers
from .models import UserProfile ,Posts , UsersCategory , CityCategory , PostsCategory
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from random import randint
import datetime



class RegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(max_length=15)
    user_type = serializers.ChoiceField(choices=UserProfile.USER_TYPE_CHOICES)
    password = serializers.CharField(write_only=True)
    company = serializers.BooleanField(default=False)
    address = serializers.CharField()
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'user_type', 'password', 'company', 'address']

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        user_type = validated_data.pop('user_type')
        is_company = validated_data.pop('company')
        address = validated_data.pop("address")

        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email']
        )
        if is_company:
            UserProfile.objects.create(user=user, phone=phone, user_type=user_type , companyId= user , address=address)
        else:
            UserProfile.objects.create(user=user, phone=phone, user_type=user_type, address=address)

        return user

class LoginSerializer(serializers.Serializer):

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        # Authenticate the user
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password")

        if not user.is_active:
            raise serializers.ValidationError("User is inactive")

        # Get the user profile and user type
        user_profile = user.profile
        user_type = user_profile.user_type

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        refresh.payload['user_type'] = user_type  # Add user type to the payload

        access_token = str(refresh.access_token)

        # Return tokens and user data (excluding password)
        return {
            'refresh': str(refresh),
            'access': access_token,
            'user_id': user.id,
            'username': user.username,
            'user_type': user_type,
        }

class UsersCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersCategory
        fields = ["id", "type"]

class CityCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CityCategory
        fields = ["id", "city"]

class PostsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostsCategory
        fields = ["id", "category"]


class UserTypeSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email')
    username = serializers.CharField(source='user.username')
    class Meta:
        model = UserProfile
        fields = ['username', 'user_type',"phone" , "address" ,"email"]

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'workAs', 'phone', 'latitude', 'longitude', 'address', 'user_type']
        depth = 1  # Optional: To include nested user details in the response

class CompanyUserSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['companyId', 'users']

    def get_users(self, obj):
        users = UserProfile.objects.filter(companyId=obj.companyId)
        return UserProfileSerializer(users, many=True).data

class JobPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Posts
        fields = ['id', 'title', 'description', 'image', 'homeowner', 'created_at', 'is_accepted','price',"status","category", "post_time" , "post_date"]
        read_only_fields = ['homeowner', 'created_at', 'is_accepted']

class HandleInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    company_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['accept', 'reject'])
