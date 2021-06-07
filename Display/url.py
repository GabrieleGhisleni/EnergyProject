from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('today-prediction/', views.today_pred, name= 'today'),
    path('tomorrow-prediction/', views.tomorrow_pred, name='tomorrow'),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name="register"),
    path('api-auth/', views.DownloadCenter, name='api')
]

if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL,
                              document_root=settings.MEDIA_ROOT)