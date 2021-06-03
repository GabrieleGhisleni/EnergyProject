from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
import os, smtplib
from email.message import EmailMessage
from KEYS.config import EMAIL_USER, EMAIL_PSW


class DisplayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Display'

    def ready(self):
        from .models import User
        def send_news_email():
            msg = EmailMessage()
            msg["Subject"] = "Renewable, thermal and load prediction in GWH for today and tomorrow"
            msg["From"] = EMAIL_USER
            msg["To"] = [user.email for user in User.objects.all()]
            msg.set_content(f"""
            The prediction for tommorow are: blabla""")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_USER, EMAIL_PSW)
                smtp.send_message(msg)

        scheduler = BackgroundScheduler()
        scheduler.add_job(send_news_email, 'cron',  day_of_week = "0-6", hour= 23)
        scheduler.start()