from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import test_email

urlpatterns = [
path("", views.index, name = "home"),
    path("blogs", views.blogs, name = "blogs"),
    path("about", views.about, name = "about"),
    path("upload", views.upload, name = "upload"),
    path("plans/", views.our_plans, name = "plans"),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('success/', views.subscription_success, name='subscription-success'),
    path("profile<int:user_id>", views.profile, name = "profile"),
    path('fullview/<int:myid>', views.blog_view, name='fullview'),
    path('login/', auth_views.LoginView.as_view(template_name='blogs/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/<int:user_id>/edit/', views.edit_profile, name='edit_profile'),
path('subscriptionview/', views.subscription_view, name='subscriptionview'),
 path('test-email/', views.test_email),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)