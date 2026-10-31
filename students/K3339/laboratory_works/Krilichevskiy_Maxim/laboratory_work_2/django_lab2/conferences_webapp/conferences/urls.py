# Маршруты приложения; общий префикс /conferences/ задан в URL проекта.
# name используется в redirect() и тегах {% url %}, чтобы не дублировать адреса.
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("participants/", views.participant_list, name="participant_list"),
    path("applications/<int:application_id>/recommendation/", views.set_recommendation, name="set_recommendation"),
    path("", views.conference_list, name="conference_list"),
    
    path("<int:conference_id>/", views.conference_detail, name="conference_detail"),
    
    path("register/", views.register, name="register"),
    
    path("login/", auth_views.LoginView.as_view(template_name="conferences/login.html"), name="login"),
    
    path("logout/",auth_views.LogoutView.as_view(next_page="conference_list"),name="logout"),
    
    path("<int:conference_id>/apply/", views.apply_to_conference, name="apply_to_conference"),
    
    path("applications/<int:application_id>/edit/", views.edit_application, name="edit_application"),
    
    path("applications/<int:application_id>/delete/", views.delete_application, name="delete_application"),
    
    path("<int:conference_id>/review/",views.add_review,name="add_review"),
]