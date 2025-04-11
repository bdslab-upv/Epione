from django.urls import path

from . import views

urlpatterns = [
    path('', views.procesado_simulacion, name="home"),
    path('procesar/', views.procesado_simulacion, name="procesar"),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),

]

