from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status , viewsets , permissions
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet ,ModelViewSet
from .serializer import RegisterSerializer, UserTypeSerializer ,JobPostSerializer , LoginSerializer , CompanyUserSerializer , HandleInvitationSerializer , UsersCategorySerializer , CityCategorySerializer, PostsCategorySerializer
from .models import User , Posts  , UserProfile , WorkerInvitation , UsersCategory , CityCategory , PostsCategory
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import IsAuthenticated ,AllowAny
from django.core.exceptions import PermissionDenied
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils.crypto import get_random_string
from rest_framework.decorators import action
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from datetime import datetime
from django.utils.timezone import now

class RegisterViewSet(viewsets.ViewSet):
    serializer_class = RegisterSerializer
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            confirmation_code = get_random_string(
                length=6, allowed_chars='1234567890')

            cache.set(f"pending_user_{email}",
                      serializer.validated_data, timeout=600)
            cache.set(f"confirmation_code_{email}",
                      confirmation_code, timeout=600)

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

class UsersCategoryViewSet(viewsets.ModelViewSet):
    queryset = UsersCategory.objects.all()
    serializer_class = UsersCategorySerializer

class CityCategoryViewSet(viewsets.ModelViewSet):
    queryset = CityCategory.objects.all()
    serializer_class = CityCategorySerializer

class PostsCategoryViewSet(viewsets.ModelViewSet):
    queryset = PostsCategory.objects.all()
    serializer_class = PostsCategorySerializer


class UserTypeViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = UserProfile.objects.filter()
    serializer_class = UserTypeSerializer

    def list(self, request, *args, **kwargs):
        user_type = request.GET.get('user_type')
        if user_type:
            queryset = UserProfile.objects.filter(user_type=user_type)
        else:
            queryset = UserProfile.objects.filter()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CompanyUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):

        company_profiles = UserProfile.objects.filter(companyId__id=company_id)
        serializer = CompanyUserSerializer(company_profiles, many=True)
        return Response(serializer.data)


class PostsFilter(filters.FilterSet):
    is_accepted = filters.NumberFilter(field_name='is_accepted', lookup_expr='exact')
    is_accepted_isnull = filters.BooleanFilter(field_name='is_accepted', lookup_expr='isnull')

    class Meta:
        model = Posts
        fields = ['title', 'description', 'status', 'price', 'homeowner', 'category']

class JobPostViewSet(viewsets.ModelViewSet):
    queryset = Posts.objects.all()
    serializer_class = JobPostSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class  = PostsFilter

    def perform_create(self, serializer):
        if self.request.user.profile.user_type == 'homeowner':
            job_post = serializer.save(homeowner=self.request.user)
            homeowner_address = self.request.user.profile.address
            workers = User.objects.filter(
                profile__user_type='worker',
                profile__address=homeowner_address
            )
            recipient_list = [
                worker.email for worker in workers if worker.email]
            if recipient_list:
                send_mail(
                    subject="'Professionals' New Job Post in Your Area",
                    message=f"A new job post has been created from {self.request.user.username} near your location in {homeowner_address}. Check it",
                    from_email="ahmadshehab11177@gmail.com",
                    recipient_list=recipient_list,
                    fail_silently=False,
                )
        else:
            raise PermissionDenied("Only homeowners can create job posts.")

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]




    def update(self, request, *args, **kwargs):
        job_post = self.get_object()
        if self.request.user.profile.user_type == 'worker':
            try:
                job_post.is_accepted = self.request.user.id
                job_post.price = request.data.get('price', job_post.price)
                # Convert the post_date (string) to datetime.date
                post_date_str = request.data.get('post_date', job_post.post_date)
                if isinstance(post_date_str, str):
                    post_date = datetime.strptime(post_date_str, "%Y-%m-%d").date()
                else:
                    post_date = post_date_str

                # Convert the post_time (string) to datetime.time
                post_time_str = request.data.get('post_time', job_post.post_time)
                if isinstance(post_time_str, str):
                    post_time = datetime.strptime(post_time_str, "%H:%M").time()
                else:
                    post_time = post_time_str

                job_post.post_time = post_time
                job_post.post_date = post_date
                job_post.save()

                return Response({'message': 'Job accepted successfully'})

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

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

        WorkerInvitation.objects.create(email=email, company=user)

        invitation_link = f"{request.build_absolute_uri('/handle-invitation/')}?email={email}&company_id={user.id}"

        send_mail(
            subject='Invitation to Join Our Company',
            message=f"Click the link to join the company: {invitation_link}",
            from_email='ahmadshehab11177@gmail.com',
            recipient_list=[email],
        )

        return Response({'message': 'Invitation sent successfully'})


class HandleInvitationView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = HandleInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        company_id = serializer.validated_data['company_id']
        action = serializer.validated_data['action']

        invitation = get_object_or_404(
            WorkerInvitation, email=email, company_id=company_id)

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


@method_decorator(csrf_exempt, name='dispatch')
class SendEmailView(View):
    def post(self, request, *args, **kwargs):
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        recipient = request.POST.get('recipient')

        if not (subject and message and recipient):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email='ahmadshehab11177@gmail.com',
                recipient_list=[recipient],
            )
            return JsonResponse({'message': 'Email sent successfully!'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
