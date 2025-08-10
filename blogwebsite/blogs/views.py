from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse
from django.core.mail import send_mail
from .models import Blogpost,Custom_user, SubscriptionPlan,UserSubscription,Payment,Category,RequestRole
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from .forms import ProfileForm,SubscriptionSelectForm
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import razorpay
from django.conf import settings
# Create your views here.

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'blogs/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'blogs/register.html')
        
        user = User.objects.create_user(username=username, password=password)
        Custom_user.objects.create(user = user)
        login(request, user) 
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
    blog_post = Blogpost.objects.all().order_by('-pub_date')
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
    blog_data = Blogpost.objects.filter(post_id = myid)
    return render(request, 'blogs/fullview.html', {'blogdata': blog_data[0], 'subscription': subscription})



def our_plans(request):
    our_plans = SubscriptionPlan.objects.all()
    return render(request, 'blogs/ourplans.html', {'plan_variable':our_plans})

@login_required
def subscribe(request, plan_id):  # <- accept plan_id from URL
    if request.method == 'POST':
        plan = SubscriptionPlan.objects.get(id=plan_id)

        UserSubscription.objects.update_or_create(
            user=request.user,
            defaults={
                'plan': plan,
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=plan.duration)
            }
        )
        return redirect('pay_method', plan_id=plan.id)


def subscription_success(request):
    return render(request, 'blogs/success.html')

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
            return render(request, 'blogs/success.html', {'plan': plan})

        elif payment_method in ['bank', 'cards', 'netbanking']:
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
    food = Blogpost.objects.filter(category__category_name__iexact='food')
    print(food)
    return render(request, "blogs/food_post.html", {'food': food})

def tech_category(request):
    tech = Blogpost.objects.filter(category__category_name__iexact='tech')
    print(tech)
    return render(request, "blogs/tech_post.html", {'tech': tech})

def life_category(request):
    life = Blogpost.objects.filter(category__category_name__iexact='lifestyle')
    print(life)
    return render(request, "blogs/life_post.html", {'life': life})

def travel_category(request):
    travel = Blogpost.objects.filter(category__category_name__iexact='travel')
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
    success= False
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        categories = Category.objects.all()
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
            blog = Blogpost(author=author,title = title,head0 = head0, category = category,chead0 = chead0,pub_date= pub_date, head1 = head1,chead1 = chead1,head2 = head2,chead2 =chead2,image_thumbnail = image_thumbnail,image1 = image1,image2 = image2)
            blog.save()
            success = True

            
    except UserSubscription.DoesNotExist:
        subscription = None
    return render(request, 'blogs/upload.html',{'subscription': subscription, 'success': success , 'categories': categories})


def send_blogger_request(request):
    if request.method == 'POST':
        existing = RequestRole.objects.filter(user=request.user).first()
        if not existing:
            RequestRole.objects.create(
                user=request.user,
                requested_role='Blogger'
            )
            
            send_mail(
                subject='New Blogger Access Request',
                message=f'User {request.user.username} has requested blogger access.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['manaschawla324@gmail.com'],  # Replace with real admin email
                fail_silently=False,
            )
        return redirect('request_pending')
    else:
        return redirect('upload_blog')
    
def request_pending(request):
    return render(request, 'blogs/request_pending.html')