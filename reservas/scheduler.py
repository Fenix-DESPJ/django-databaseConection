from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.core.management import call_command
from django.conf import settings

def enviar_recordatorios_job():
    """Función independiente para que el scheduler pueda serializarla correctamente."""
    call_command('enviar_recordatorios')

def start():
    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Usamos la función nombrada en lugar de una lambda
    scheduler.add_job(
        enviar_recordatorios_job,
        'interval',
        minutes=5,
        name='enviar_recordatorios_whatsapp_job',
        jobstore='default',
        replace_existing=True,
    )

    scheduler.start()