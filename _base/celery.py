import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_base.settings')

app = Celery('RequestsManager')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django _base configs.
app.autodiscover_tasks()

# timezone
app.conf.timezone = settings.TIME_ZONE

app.conf.task_default_queue = 'default'
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['pickle', 'json']

app.conf.task_routes = {
    'request_.tasks.*': {'queue': 'request'}
}


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
