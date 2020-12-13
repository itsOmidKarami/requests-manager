from django.contrib import admin
# Register your models here.
from django import forms
from django.utils import timezone
from safedelete.admin import SafeDeleteAdmin

from request_.models import Request


class RequestForm(forms.ModelForm):
    def clean_due_time(self):
        if self.cleaned_data['due_time'] < timezone.now():
            raise forms.ValidationError("Due-Time can't be before current time")
        return self.cleaned_data['due_time']


@admin.register(Request)
class RequestAdmin(SafeDeleteAdmin):
    form = RequestForm
    list_display = ('id', 'creator', 'status', 'method', 'due_time', 'response_http_status')
    readonly_fields = ('id', 'status', 'response_body', 'response_http_status', 'creator')
    search_fields = ('id', 'response_http_status', 'url', 'method', 'status',
                     'creator__username') + SafeDeleteAdmin.search_fields
    list_filter = ('status', 'method', 'response_http_status')

    def creator(self, obj: Request):
        return obj.creator.username

    creator.admin_order_field = 'creator__username'
    creator.short_description = 'creator'

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Request.objects.all()
        else:
            return Request.objects.filter(creator=request.user)

    def save_model(self, request, obj: Request, form, change):
        obj.creator = request.user
        super(RequestAdmin, self).save_model(request, obj, form, change)
