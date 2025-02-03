from rest_framework.routers import SimpleRouter
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# Create the router
router = SimpleRouter()
router.register('users', views.UserTypeViewSet, basename="user-types")
router.register('register', views.RegisterViewSet, basename="register")
router.register(r'jobposts', views.JobPostViewSet, basename='jobpost')
router.register('posts-category', views.PostsCategoryViewSet, basename='postscategory')
router.register('users-category', views.UsersCategoryViewSet, basename='userscategory')
router.register('city-category', views.CityCategoryViewSet, basename='cityCategory')
<<<<<<< HEAD
=======
router.register('chats', views.ChatViewSet, basename='chat')
router.register('messages', views.MessagesViewSet, basename='message')
>>>>>>> 2aac61f (a)
""" router.register('accept-job', views.jobAcceptanceView, basename='acceptJob') """

# Note: LoginView is not a ViewSet; it should not be registered with a router.
# Define LoginView separately in urlpatterns if needed.

urlpatterns = [
    # JWT authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Include the router URLs
    path('', include(router.urls)),
    path('company-users/<int:company_id>/', views.CompanyUsersView.as_view(), name='company-users'),
    # Add LoginView explicitly (not in the router)
    path('api/login/', views.LoginView.as_view(), name='login'),
    path('send-invitation/', views.SendInvitationView.as_view(), name='send_invitation'),
    path('handle-invitation/', views.HandleInvitationView.as_view(), name='handle_invitation'),
    path('send-email/', views.SendEmailView.as_view(), name='send_email'),
]
