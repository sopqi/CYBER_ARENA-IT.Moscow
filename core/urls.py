from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    #основные
    path('', views.home, name='home'),
    path('map/', views.map_view, name='map'),
    path('book/<int:pc_id>/', views.book_computer, name='book_computer'),
    path('profile/', views.profile, name='profile'),

    # авторизаация
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # не трогать, это апи для ажах
    path('api/get-groups/', views.get_groups_ajax, name='get_groups_ajax'),

    # репутация комменты профиль
    path('user/<str:username>/', views.profile_view, name='profile_view'),
    path('user/<int:user_id>/rep/', views.toggle_reputation, name='toggle_rep'),
    path('user/<str:username>/comment/', views.add_profile_comment, name='add_comment'),

    #турниры
    path('tournaments/', views.tournament_list, name='tournament_list'),
    path('tournaments/create/', views.tournament_create, name='tournament_create'),
    path('tournaments/<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('tournaments/<int:pk>/register/', views.tournament_register, name='tournament_register'),

    #отмены бронирования и турниров
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('tournaments/<int:pk>/unregister/', views.tournament_unregister, name='tournament_unregister'),
]