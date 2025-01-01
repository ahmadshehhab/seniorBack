from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status , viewsets , permissions
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet ,ModelViewSet
from .serializer import RegisterSerializer, UserTypeSerializer ,JobPostSerializer , LoginSerializer , CompanyUserSerializer , HandleInvitationSerializer
from .models import User , Posts  , UserProfile , WorkerInvitation
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import IsAuthenticated ,AllowAny 
from django.core.exceptions import PermissionDenied
from twilio.rest import Client
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils.crypto import get_random_string
from rest_framework.decorators import action

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['user_type'] = user.profile.user_type
    refresh['company_id'] = user.id if user.profile.user_type == 'company' else None
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }



class RegisterViewSet(viewsets.ViewSet):
    serializer_class = RegisterSerializer
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            confirmation_code = get_random_string(length=6, allowed_chars='1234567890')

            # Store user data and confirmation code in the cache
            cache.set(f"pending_user_{email}", serializer.validated_data, timeout=600)  # 10 minutes
            cache.set(f"confirmation_code_{email}", confirmation_code, timeout=600)

            # Send the confirmation email
            send_mail(
                subject="Your Confirmation Code",
                message=f"Your confirmation code is {confirmation_code}. It expires in 10 minutes.",
                from_email="your_email@example.com",
                recipient_list=[email],
                fail_silently=False,
            )

            return Response({'message': 'Confirmation code sent to email.'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='confirm')
    def confirm_registration(self, request, *args, **kwargs):
        email = request.data.get('email')
        code = request.data.get('code')

        # Retrieve the stored code and user data
        stored_code = cache.get(f"confirmation_code_{email}")
        user_data = cache.get(f"pending_user_{email}")

        if not stored_code or not user_data:
            return Response({'error': 'Invalid or expired confirmation code.'}, status=status.HTTP_400_BAD_REQUEST)

        if stored_code == code:
            # Save the user to the database
            serializer = self.serializer_class(data=user_data)
            if serializer.is_valid():
                serializer.save()
                # Clear the cache
                cache.delete(f"confirmation_code_{email}")
                cache.delete(f"pending_user_{email}")
                return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)

        return Response({'error': 'Invalid confirmation code.'}, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserTypeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = UserTypeSerializer

class CompanyUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        # Query UserProfile based on companyId
        company_profiles = UserProfile.objects.filter(companyId__id=company_id)
        serializer = CompanyUserSerializer(company_profiles, many=True)
        return Response(serializer.data)

class JobPostViewSet(viewsets.ModelViewSet):
    queryset = Posts.objects.all()
    serializer_class = JobPostSerializer

    def perform_create(self, serializer):
        # Only homeowners can create job posts
        if self.request.user.profile.user_type == 'homeowner':
            serializer.save(homeowner=self.request.user)
        else:
            raise PermissionDenied("Only homeowners can create job posts.")

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]  # Only authenticated users can create job posts
        return [permissions.AllowAny()]  # All users can view job posts (workers can only view, not create)

    def list(self, request, *args, **kwargs):
        # Workers can only see available jobs (not accepted)
        queryset = Posts.objects.filter()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        # Workers can accept a job
        job_post = self.get_object()
        if self.request.user.profile.user_type == 'worker':
            
            job_post.is_accepted = self.request.user.id
            job_post.save()
            return Response({'message': 'Job accepted successfully'})
        return Response({'message': 'You are not authorized to accept this job'}, status=403)

class SendInvitationView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.profile.user_type != 'company':
            return Response({'error': 'Only companies can send invitations'}, status=403)

        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=400)

        # Create the invitation
        WorkerInvitation.objects.create(email=email, company=user)

        # Send email to the worker
        invitation_link = f"{request.build_absolute_uri('/handle-invitation/')}?email={email}&company_id={user.id}"
        
        send_mail(
            subject='Invitation to Join Our Company',
            message=f"Click the link to join the company: {invitation_link}",
            from_email='ahmadshehab11177@gmail.com',
            recipient_list=[email],
        )

        return Response({'message': 'Invitation sent successfully'})

from django.db.models import Q

class HandleInvitationView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = HandleInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        company_id = serializer.validated_data['company_id']
        action = serializer.validated_data['action']

        invitation = get_object_or_404(WorkerInvitation, email=email, company_id=company_id)

        if action == 'accept':
            invitation.is_accepted = True
            user = get_object_or_404(User, email=email)
            profile = user.profile
            profile.companyId_id = company_id
            profile.user_type = 'worker'
            profile.save()
        elif action == 'reject':
            invitation.is_rejected = True

        invitation.save()
        return Response({'message': f'Invitation {action}ed successfully'})






""" def send_sms_verification(phone_number, verification_code):
    Send SMS with a verification code using Twilio
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    message = client.messages.create(
        body=f"Your verification code is: {verification_code}",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone_number
    )
    
    return message.sid




class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        # Deserialize and validate the login data
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # You no longer need to access password directly here
            user = authenticate(username=serializer.validated_data['username'], password=request.data['password'])

            if user is not None:
                # Generate a random 6-digit verification code
                verification_code = randint(100000, 999999)

                # Store the verification code in the session with an expiration time (e.g., 5 minutes)
                request.session['verification_code'] = verification_code
                request.session['verification_code_expiry'] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()
  # 5-minute expiry

                # Send the SMS with the verification code
                send_sms_verification(user.profile.phone, verification_code)

                # Return the JWT tokens and a message indicating that verification is needed
                return Response({
                    'message': 'Verification code sent to your phone',
                    'access': serializer.validated_data['access'],
                    'refresh': serializer.validated_data['refresh'],
                    'user_id': serializer.validated_data['user_id'],
                    'username': serializer.validated_data['username'],
                    'user_type': serializer.validated_data['user_type']
                }, status=status.HTTP_200_OK)

            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import datetime

class VerifyCodeView(APIView):
    def post(self, request):
        verification_code = request.data.get('verification_code')

        # Check if the verification code matches
        if 'verification_code' not in request.session:
            return Response({"error": "No verification code sent."}, status=status.HTTP_400_BAD_REQUEST)

        stored_code = request.session.get('verification_code')
        expiry_time_str = request.session.get('verification_code_expiry')

        # Convert the expiry time string back to a datetime object
        try:
            expiry_time = datetime.datetime.fromisoformat(expiry_time_str)
        except ValueError:
            return Response({"error": "Invalid expiry time format."}, status=status.HTTP_400_BAD_REQUEST)

        # Compare the current time with the expiry time
        if datetime.datetime.now() > expiry_time:
            return Response({"error": "Verification code expired."}, status=status.HTTP_400_BAD_REQUEST)

        if str(verification_code) == str(stored_code):
            return Response({"message": "Phone number verified successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)


 """