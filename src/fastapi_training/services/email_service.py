import time
from ..core.celery_app import celery_app

@celery_app.task(name="send_welcome_email_task")
def send_welcome_email(email_address: str):
    """
    Mock pushing an email out using a simulated delay.
    In a real application, you would use a library like aiosmtplib or an API like SendGrid/SES.
    """
    print(f"[Celery Worker] Preparing to send welcome email to: {email_address}...")
    
    # Simulate connection to SMTP server or API call delay (3 seconds)
    time.sleep(3) 
    
    print(f"[Celery Worker] Successfully sent welcome email to {email_address}!")
    return f"Email sent to {email_address}"

