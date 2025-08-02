from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
# Create your models here.

class Blogpost(models.Model):
    author = models.CharField(max_length=100, default="Anonymous")
    post_id=models.AutoField(primary_key=True)
    title=models.CharField(max_length=50)
    head0 = models.CharField(max_length=500, default="")
    head1= models.CharField(max_length=500, default="")
    head2= models.CharField(max_length=500, default="")
    chead0= models.CharField(max_length=5000, default="")
    chead1=models.CharField(max_length=5000, default="")
    chead2=models.CharField(max_length=5000, default="")
    pub_date=models.DateField()
    image_thumbnail = models.ImageField(upload_to="blogs/images", blank=True, null=True)
    image1 = models.ImageField(upload_to="blogs/images", blank=True, null=True)
    image2 = models.ImageField(upload_to="blogs/images", blank=True, null=True)

    def __str__(self):
        return str(self.title)

class Custom_user(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True, blank=True)
    profile_picture = models.ImageField(upload_to="blogs/images", blank=True, null=True)
    first_name = models.CharField(max_length=50, default="not defined")
    last_name = models.CharField(max_length=50, default="not defined")
    email = models.EmailField(max_length=60, default="not defined")
    country = models.CharField(max_length=50, default= "not defined")
    state = models.CharField(max_length=50, default= "not defined")
    city = models.CharField(max_length=50, default= "not defined")
    mobile_number = models.BigIntegerField(default=0)
    alternate_mobile_number = models.BigIntegerField(default=0)
    pincode = models.IntegerField(default=0)

    
    def __str__(self):
        return str(self.first_name)
    
    

class SubscriptionPlan(models.Model):
    PLAN_CHOICES = (
        ('Regular', 'Regular'),
        ('Standard', 'Standard'),
        ('Premium', 'Premium'),
    )
    name = models.CharField(max_length=50, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration of plan in days")
    features = models.TextField(help_text="Enter one feature per line", blank=True)
    is_active = models.BooleanField(default=True)
    highlight = models.BooleanField(default=False, help_text="Use to highlight in frontend")

    def feature_list(self):
        return self.features.strip().split('\n')

    def __str__(self):
        return f"{self.name} - ₹{self.price}"
    
    
class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def save(self,*args, **kwargs):
        if self.start_date and not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration)
        super().save(*args, **kwargs)
            
    def is_valid(self):
        if self.is_active:
            if self.end_date and self.end_date >= timezone.now():
                return True
            else:
                return False
            
    def days_left(self):
        if self.is_active:
            if self.end_date:
                delta = self.end_date - timezone.now()
                return max(delta.days, 0)
        return 0
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"
    
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('upi', 'UPI'),
        ('bank', 'Bank Transfer'),
        ('razorpay', 'Razorpay'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    amount = models.IntegerField()
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # Razorpay Payment ID or UTR
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - {self.status}"

