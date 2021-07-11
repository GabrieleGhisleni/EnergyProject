from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
import os, smtplib
from email.message import EmailMessage

class DisplayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Display'

    def ready(self):
        from .models import User
        def send_news_email():
            email_user = os.environ.get('EMAIL_USER')
            email_psw =  os.environ.get('EMAIL_psw')
            if email_psw:
                msg = EmailMessage()
                msg["Subject"] = "Renewable, thermal and load prediction in GWH for today and tomorrow"
                msg["From"] = email_user
                msg["To"] = [user.email for user in User.objects.all()]
                msg.set_content(f"""
                The prediction for tommorow are: blabla""")
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(email_user, email_psw)
                    smtp.send_message(msg)

        scheduler = BackgroundScheduler()
        scheduler.add_job(send_news_email, 'cron',  day_of_week = "0-6", hour= 23)
        scheduler.start()