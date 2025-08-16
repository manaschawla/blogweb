from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
import base64

from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives

import pyotp
import qrcode
from io import BytesIO
import razorpay

from .models import (
    Blogpost,
    Custom_user,
    SubscriptionPlan,
    UserSubscription,
    Payment,
    Category,
    RequestRole,
    LoginInstance,
)
from .forms import ProfileForm, SubscriptionSelectForm

# Create your views here.
def otp_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.custom_user.is_2fa_enabled:
            if not request.session.get("is_2fa_verified", False):
                messages.warning(request, "Please verify OTP to continue.")
                return redirect("enable_2fa")
        return view_func(request, *args, **kwargs)
    return wrapper


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'blogs/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'blogs/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'blogs/register.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        custom_user = Custom_user.objects.create(user=user, email=email)
        
        login(request, user)


        message = render_to_string('blogs/emails/welcome_email.html', {
            'custom_user': custom_user,
            'site_url': 'https://yourwebsite.com' 
        })

        email_message = EmailMessage(
            subject="Welcome to Our Blog!",
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_message.content_subtype = "html" 
        email_message.send()

        messages.success(request, "Registration successful! A welcome email has been sent.")
        return redirect('/')
    
    return render(request, 'blogs/register.html')


@login_required
def edit_profile(request, user_id):
    profile = Custom_user.objects.get(user__id=user_id)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', user_id=user_id)
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'blogs/edit_profile.html', {'form': form})

@otp_required
def index(request):
    blog_post = Blogpost.objects.all().order_by('-pub_date','-post_id')

    first_post = blog_post[0] 
    second_post = blog_post[1] 
    print(first_post)
    print(second_post)

    params = {'first_post': first_post, 'second_post': second_post}
    return render(request, 'blogs/index.html', params)



def about(request):
    return render( request, 'blogs/about.html')

@login_required
def profile(request, user_id):
    user = User.objects.get(id=user_id)
    profile = Custom_user.objects.get(user=user)
    print(profile)
    return render(request, 'blogs/profile.html', {'user_obj': user, 'profile': profile})


def contact(request):
    return render( request, 'index.html')


def blogs(request):
    blog_post = Blogpost.objects.filter(deleted_at__isnull=True).order_by('-pub_date')
    print(blog_post)
    params = {'allblogs': blog_post}
    return render( request, 'blogs/blogpost.html',params)

def search(request):
    return render( request, 'index.html')

@login_required
def blog_view(request, myid):
    try:
        subscription = UserSubscription.objects.get(user=request.user)
    except UserSubscription.DoesNotExist:
        subscription = None

    blog = get_object_or_404(Blogpost, post_id=myid) 
    blog.views += 1
    blog.save(update_fields=['views'])

    return render(request, 'blogs/fullview.html', {
        'blogdata': blog,
        'subscription': subscription
    })




def toggle_like(request, blog_id):
    blog = get_object_or_404(Blogpost, post_id=blog_id)

    if request.user in blog.likes.all():
        blog.likes.remove(request.user)
    else:
        blog.likes.add(request.user)

    blog.views = max(0, blog.views - 1)
    blog.save(update_fields=['views'])

    return redirect('fullview', blog_id)



def our_plans(request):
    our_plans = SubscriptionPlan.objects.all()
    return render(request, 'blogs/ourplans.html', {'plan_variable':our_plans})

@login_required
def subscribe(request, plan_id):
    if request.method == 'POST':
        plan = SubscriptionPlan.objects.get(id=plan_id)

        subscription, created = UserSubscription.objects.update_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=plan.duration)
            }
        )


        return redirect('pay_method', plan_id=plan.id)


def subscription_success(request, subscription_id):
    subscription = get_object_or_404(UserSubscription, id=subscription_id)
    send_invoice_email(request.user, subscription)
    messages.success(request, "Subscription purchased successfully. Invoice sent to your email.")
    return render(request, 'blogs/success.html', {'subscription': subscription})


def subscription_view(request):
    try:
        subscription = UserSubscription.objects.get(user=request.user)
    except UserSubscription.DoesNotExist:
        subscription = None

    return render(request, 'blogs/subscription_view.html', {'subscription': subscription})


def pay_method(request,plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        if payment_method in ['upi', 'cod']:
            Payment.objects.create(
                user=request.user,
                plan=plan,
                payment_method=payment_method,
                status='success',
                amount=plan.price,
            )
            subscription = UserSubscription.objects.get(user=request.user)
            send_invoice_email(request.user, subscription)
            return render(request, 'blogs/success.html', {'plan': plan})
        

        elif payment_method in ['bank', 'cards', 'netbanking']:
            subscription = UserSubscription.objects.get(user=request.user)
            send_invoice_email(request.user, subscription)
            return redirect('razorpay_payment', plan_id=plan.id)

    return render(request, 'blogs/select_pay_method.html', {'plan': plan})


    

def test_email(request):
    send_mail(
        subject='Test Email',
        message='This is a test email sent via console backend.',
        from_email='admin@example.com',
        recipient_list=['manaschawla324@gmail.com'],
        fail_silently=False,
    )
    return HttpResponse("Test email sent. Check your terminal.")

def razorpay_payment_view(request,plan_id):
    plan = get_object_or_404(SubscriptionPlan, pk=plan_id)
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    payment = client.order.create({
        "amount": int(plan.price * 100), 
        "currency": "INR",
        "payment_capture": 1
    })

    context = {
        'plan': plan,
        'payment': payment,
        'razorpay_key': settings.RAZORPAY_KEY_ID
    }

    return render(request, 'blogs/payment_razorpay.html', context)

def payment_success(request, plan_id):
    return render(request, 'blogs/success.html')


def food_category(request):
    food = Blogpost.objects.filter(category__category_name__iexact='food', deleted_at__isnull=True)
    print(food)
    return render(request, "blogs/food_post.html", {'food': food})

def tech_category(request):
    tech = Blogpost.objects.filter(category__category_name__iexact='tech', deleted_at__isnull=True)
    print(tech)
    return render(request, "blogs/tech_post.html", {'tech': tech})

def life_category(request):
    life = Blogpost.objects.filter(category__category_name__iexact='lifestyle', deleted_at__isnull=True)
    print(life)
    return render(request, "blogs/life_post.html", {'life': life})

def travel_category(request):
    travel = Blogpost.objects.filter(category__category_name__iexact='travel', deleted_at__isnull=True)
    print(travel)
    return render(request, "blogs/travel_post.html", {'travel': travel})

def upload_check(request):
    custom_user = request.user.custom_user
    if custom_user.role == 'blogger':
        return render(request, 'blogs/upload.html')
    
    else:
        existing_request = RequestRole.objects.filter(user=request.user).first()
        
        if existing_request:
            if existing_request.is_approved:
                return render(request, 'blogs/request_approved.html')
            else:
                return render(request, 'blogs/request_pending.html')
        else:
            return render(request, 'blogs/request_access.html')  
        
@login_required
def upload(request):
    success = False
    categories = Category.objects.all()  

    try:
        subscription = UserSubscription.objects.get(user=request.user)

        if request.method == "POST":
            author = request.POST.get('author')
            title = request.POST.get('title')
            head0 = request.POST.get('head0')
            chead0 = request.POST.get('chead0')
            head1 = request.POST.get('head1')
            category_id = request.POST.get('category')
            category = Category.objects.get(id=category_id)
            chead1 = request.POST.get('chead1')
            chead2 = request.POST.get('chead2')
            head2 = request.POST.get('head2')
            pub_date = request.POST.get('pub_date')
            image_thumbnail = request.FILES.get('image_thumbnail')
            image1 = request.FILES.get('image1')
            image2 = request.FILES.get('image2')

            blog = Blogpost(
                author=author,
                title=title,
                head0=head0,
                category=category,
                chead0=chead0,
                pub_date=pub_date,
                head1=head1,
                chead1=chead1,
                head2=head2,
                chead2=chead2,
                image_thumbnail=image_thumbnail,
                image1=image1,
                image2=image2
            )
            blog.save()
            success = True

    except UserSubscription.DoesNotExist:
        subscription = None

    return render(
        request,
        'blogs/upload.html',
        {'subscription': subscription, 'success': success, 'categories': categories}
    )



def send_blogger_request(request):
    if request.method == 'POST':
        existing = RequestRole.objects.filter(user=request.user).first()
        if not existing:
            RequestRole.objects.create(
                user=request.user,
                requested_role='Blogger'
            )

            admin_email = 'manaschawla324@gmail.com'
            subject = "New Blogger Access Request"

            html_content = render_to_string(
                "blogs/emails/request_role.html",
                {"user": request.user, "current_year": datetime.now().year}
            )

            email = EmailMessage(
                subject,
                html_content,
                settings.DEFAULT_FROM_EMAIL,
                [admin_email]
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)  # Forces error if something goes wrong

            return redirect('request_pending')

        return redirect('request_pending')
    return redirect('upload_blog')


    
def request_pending(request):
    return render(request, 'blogs/request_pending.html')

def send_invoice_email(user, subscription):
    recipient_email = user.custom_user.email
    subject = f"Invoice for your {subscription.plan.name} Subscription"
    message = render_to_string('blogs/emails/invoice_email.html', {
        'custom_user': user.custom_user,
        'subscription': subscription,
    })
    
    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email]
    )
    email.content_subtype = "html" 
    email.send()
    
@login_required
def my_blogs(request):
    blogs = Blogpost.objects.filter(author = request.user,deleted_at__isnull=True)
    return render(request, 'blogs/author_blogs.html', {'blogdata': blogs})

@login_required
def delete_blog(request, post_id):
    blog = get_object_or_404(Blogpost, post_id=post_id, author=request.user)
    blog.deleted_at = timezone.now()
    blog.save(update_fields=['deleted_at'])
    messages.success(request, f'Your blog "{blog.title}" was deleted successfully.')
    return redirect('my_blogs')
    

@login_required
def edit_blog(request, post_id):
    blog = get_object_or_404(Blogpost, pk=post_id)

    if request.method == "POST":
        
        blog.title = request.POST.get("title")
        blog.head0 = request.POST.get("head0")
        blog.head1 = request.POST.get("head1")
        blog.head2 = request.POST.get("head2")
        blog.chead0 = request.POST.get("chead0")
        blog.chead1 = request.POST.get("chead1")
        blog.chead2 = request.POST.get("chead2")

        
        if 'image_thumbnail' in request.FILES:
            blog.image_thumbnail = request.FILES['image_thumbnail']
        if 'image1' in request.FILES:
            blog.image1 = request.FILES['image1']
        if 'image2' in request.FILES:
            blog.image2 = request.FILES['image2']

        
        blog.edited_by = request.user
        blog.edited_at = timezone.now()

        blog.save()

        messages.success(request, "Blog updated successfully.")
        return redirect("my_blogs")

    return render(request, "blogs/edit_blog.html", {"blog": blog})
    

class CustomLoginView(LoginView):
    template_name = 'blogs/login.html'

    def form_valid(self, form):
        # ✅ Call parent form_valid → logs user in
        response = super().form_valid(form)

        # ✅ Track login attempt
        ip = self.get_client_ip()
        device = self.request.META.get('HTTP_USER_AGENT', 'Unknown device')

        LoginInstance.objects.create(
            user=self.request.user,
            ip_address=ip,
            device_info=device
        )

        # ✅ Send email notification
        html_message = render_to_string('blogs/emails/login_notification.html', {
            'user': self.request.user,
            'ip': ip,
            'device': device,
        })
        plain_message = strip_tags(html_message)

        send_mail(
            subject="New Login Detected",
            message=plain_message,
            from_email="noreply@yourwebsite.com",
            recipient_list=[self.request.user.email],
            html_message=html_message
        )

        # ✅ Check if 2FA is enabled
        if self.request.user.custom_user.is_2fa_enabled:
            # mark user as "pending OTP verification"
            self.request.session["is_2fa_verified"] = False  
            return redirect("two_factor_auth")  # force OTP step before home

        # otherwise normal login success
        return response
    

    def get_client_ip(self):
        """Extract the IP address from request"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')
    
@login_required
def login_history(request):
    logins = LoginInstance.objects.filter(user=request.user).order_by('-login_time')
    return render(request, 'blogs/login_history.html', {'logins': logins})

@login_required
def two_factor_auth(request):
    custom_user = request.user.custom_user  

    # Generate secret key if not present
    if not custom_user.otp_secret:
        custom_user.otp_secret = pyotp.random_base32()
        custom_user.is_2fa_enabled = True  
        custom_user.save()

    totp = pyotp.TOTP(custom_user.otp_secret)

    if request.method == "POST":
        user_otp = request.POST.get("otp")

        if totp.verify(user_otp, valid_window=1):  
            request.session["is_2fa_verified"] = True
            messages.success(request, "✅ OTP verified successfully! Welcome back.")  # ✅ success message
            return redirect("home")  
        else:
            messages.error(request, "❌ Invalid or expired OTP. Please try again.")  # ❌ error message
            return redirect("two_factor_auth")

    else:
        qr_code = None  

        # Generate QR code if user hasn’t enabled 2FA yet
        if not custom_user.is_2fa_enabled:
            otp_uri = totp.provisioning_uri(
                name=custom_user.email,
                issuer_name="MyBlogSite"
            )
            img = qrcode.make(otp_uri)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_code = base64.b64encode(buffer.getvalue()).decode()

        return render(request, "blogs/otp.html", {"qr_code": qr_code})




