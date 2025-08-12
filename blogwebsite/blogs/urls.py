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
    path('success/', views.subscription_success, name='subscription-success'),
    path("profile<int:user_id>", views.profile, name = "profile"),
    path('fullview/<int:myid>', views.blog_view, name='fullview'),
    path('login/', auth_views.LoginView.as_view(template_name='blogs/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/<int:user_id>/edit/', views.edit_profile, name='edit_profile'),
path('subscriptionview/', views.subscription_view, name='subscriptionview'),
 path('test-email/', views.test_email),
  path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
  path('paypage/<int:plan_id>/', views.pay_method, name='pay_method'),
  path('razorpay/<int:plan_id>/', views.razorpay_payment_view, name='razorpay_payment'),
path('payment/success/<int:plan_id>/', views.payment_success, name='payment_success'),
path("food", views.food_category, name = "food"),
path("tech", views.tech_category, name = "tech"),
path("lifestyle", views.life_category, name = "lifestyle"),
path("travel", views.travel_category, name = "travel"),
path("upload_check", views.upload_check, name = "upload_check"),
path('send-blogger-request/', views.send_blogger_request, name='send_blogger_request'),
path('request-pending/', views.request_pending, name='request_pending'), 
path('blog/<int:blog_id>/like/', views.toggle_like, name='toggle_like'),
path('myblogs', views.my_blogs, name='myblogs'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)