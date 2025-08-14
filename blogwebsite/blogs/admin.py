from django.contrib import admin
from .models import Blogpost, Custom_user, SubscriptionPlan, UserSubscription, Payment, Category, RequestRole,LoginInstance
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from datetime import datetime
from django.conf import settings

from django.conf import settings
# Register your models here.
admin.site.register(Blogpost)
admin.site.register(Custom_user)
admin.site.register(Category)
admin.site.register(LoginInstance)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'is_active', 'highlight')
    list_filter = ('is_active', 'highlight')
    search_fields = ('name',)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'is_active', 'end_date')
    list_filter = ('is_active', 'plan')
    search_fields = ('user__username',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'payment_method',
                    'status', 'amount', 'created_at')
    list_filter = ('payment_method', 'status')
    search_fields = ('user__username', 'plan__name', 'payment_id')


@admin.register(RequestRole)
class RequestRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'requested_role', 'is_approved')

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = RequestRole.objects.get(pk=obj.pk)
            if not old_obj.is_approved and obj.is_approved:
                custom_user = Custom_user.objects.get(user=obj.user)
                custom_user.role = 'Blogger'
                custom_user.save()

                subject = "Blogger Access Approved"

                html_content = render_to_string(
                    "blogs/emails/request_approved.html",
                    {"user": obj.user, "current_year": datetime.now().year}
                )

                email = EmailMessage(
                    subject,
                    html_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [custom_user.email]
                )
                email.content_subtype = "html"
                email.send(fail_silently=False)

        super().save_model(request, obj, form, change)
