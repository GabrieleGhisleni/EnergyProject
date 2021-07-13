from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
import os, smtplib, sys, smtplib
import Code.meteo_managers as dbs
import pandas as pd
from email.message import EmailMessage


class DisplayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Display'
    def ready(self):
        def get_data():
            db = dbs.RedisDB()
            today = pd.DataFrame(db.get_data(day='today'))
            tomorrow = pd.DataFrame(db.get_data(day='tomorrow'))
            df = today.append(tomorrow, ignore_index=True)
            return df[['dates', 'wind', 'hydro', 'geothermal', 'biomass', 'thermal', 'load']]

        def create_msg(data):
            msg = EmailMessage()
            msg['Subject'] = 'Renewable Predictions!'
            from .views import getTableHTML
            msg.add_alternative(getTableHTML(data), subtype='html')
            return msg

        def newsletter():
            email_energy_bdt = 'energy.project.bdt@gmail.com'
            psw = 'slbsflwergruvxbs'
            from django.contrib.auth.models import User
            listone = [user.email for user in User.objects.all()]
            msg = create_msg(get_data())
            for user in listone:
                try:
                    server = smtplib.SMTP('smtp.gmail.com:587')
                    server.starttls()
                    server.login(email_energy_bdt, psw)
                    server.sendmail(email_energy_bdt, user, msg.as_string())
                    print(f'Sended email to {user}')
                except Exception as e:
                    print(e)

        scheduler = BackgroundScheduler()
        hours = os.getenv('NEWS_RATE', '8,20')
        if hours == 'now': newsletter()
        else:
            scheduler.add_job(newsletter, 'cron',  day_of_week = "0-6", hour=hours)
            scheduler.start()