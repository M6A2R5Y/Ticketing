from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Dashboard and Ticket workflows
    path('', views.dashboard, name='dashboard'),
    path('ticket/new/', views.ticket_create, name='ticket_create'),
    path('ticket/<int:pk>/', views.ticket_detail, name='ticket_detail'),
    
    # Chatbot endpoint
    path('api/chat/', views.chatbot_api, name='chatbot_api'),
    
    # Auth paths
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
