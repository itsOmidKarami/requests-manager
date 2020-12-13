import logging

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from safedelete import SOFT_DELETE
from safedelete.models import SafeDeleteModel
from simple_history.models import HistoricalRecords

logger = logging.getLogger(__name__)


class Request(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    history = HistoricalRecords()

    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    url = models.CharField(max_length=2048, null=False, blank=False)

    METHOD_TYPE_GET = 'get'
    METHOD_TYPE_POST = 'post'
    METHOD_TYPE_PUT = 'put'
    METHOD_TYPE_PATCH = 'patch'
    METHOD_TYPE_DELETE = 'delete'

    METHOD_TYPE_CHOICES = (
        (METHOD_TYPE_GET, 'GET'),
        (METHOD_TYPE_POST, 'POST'),
        (METHOD_TYPE_PUT, 'PUT'),
        (METHOD_TYPE_PATCH, 'PATCH'),
        (METHOD_TYPE_DELETE, 'DELETE'),
    )

    method = models.CharField(choices=METHOD_TYPE_CHOICES, default=METHOD_TYPE_GET, max_length=6)
    params = JSONField(default=dict, blank=True)
    data = JSONField(default=dict, blank=True)

    due_time = models.DateTimeField(null=False, blank=False)

    STATUS_TYPE_INITIAL = 'INIT'
    STATUS_TYPE_PENDING = 'PENDING'
    STATUS_TYPE_PROCESSING = 'PROCESSING'
    STATUS_TYPE_SUCCESSFUL = 'SUCCESSFUL'
    STATUS_TYPE_FAILED = 'FAILED'
    STATUS_TYPE_CANCELED = 'CANCELED'

    STATUS_TYPE_CHOICES = (
        (STATUS_TYPE_INITIAL, _('Initial')),
        (STATUS_TYPE_PENDING, _('Pending')),
        (STATUS_TYPE_PROCESSING, _('Processing')),
        (STATUS_TYPE_SUCCESSFUL, _('Successful')),
        (STATUS_TYPE_FAILED, _('Failed')),
        (STATUS_TYPE_CANCELED, _('Canceled')),
    )

    status = models.CharField(choices=STATUS_TYPE_CHOICES, default=STATUS_TYPE_INITIAL, max_length=10)

    response_http_status = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(limit_value=999), MinValueValidator(100)], null=True)
    response_body = JSONField(blank=True, null=True)


@receiver(post_save, sender=Request)
def post_save_request(sender, instance: Request, **kwargs):
    if instance.status == Request.STATUS_TYPE_INITIAL:
        from request_.tasks import execute_request
        execute_request.apply_async(args=(instance.id, ), eta=instance.due_time)
        instance.status = Request.STATUS_TYPE_PENDING
        instance.save(update_fields=['status'])
