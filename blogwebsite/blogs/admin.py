from django.contrib import admin
from .models import Blogpost, Custom_user,SubscriptionPlan,UserSubscription,Payment
# Register your models here.
admin.site.register(Blogpost)
admin.site.register(Custom_user)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display= ('name', 'price', 'duration', 'is_active', 'highlight')
    list_filter =('is_active', 'highlight')
    search_fields =('name',)
    
@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display =('user', 'plan', 'start_date', 'is_active', 'end_date')
    list_filter = ('is_active', 'plan')
    search_fields = ('user__username',)
    
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'payment_method', 'status', 'amount', 'created_at')
    list_filter = ('payment_method', 'status')
    search_fields = ('user__username', 'plan__name', 'payment_id')