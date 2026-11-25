from celery import shared_task


@shared_task(name="core.ping")
def ping():
    """Round-trip task used to verify that the Celery worker is reachable."""
    return "pong"
