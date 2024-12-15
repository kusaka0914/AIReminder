import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIReminder.AIReminder.settings')

application = get_wsgi_application()
