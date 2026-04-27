from django.urls import path
from . import views

app_name = 'cinema'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),  
    path('contact/', views.contact, name='contact'),
    
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('movie/<int:movie_id>/book/', views.book_ticket, name='book_ticket'),
    path('booking/<str:booking_reference>/', views.booking_confirmation, name='booking_confirmation'),
    
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/<str:booking_reference>/', views.payment, name='payment'),

    path('search/', views.search_movies, name='search'),
]