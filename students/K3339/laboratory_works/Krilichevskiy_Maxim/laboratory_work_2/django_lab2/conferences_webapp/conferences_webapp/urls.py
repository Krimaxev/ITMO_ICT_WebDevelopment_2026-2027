"""Главные маршруты: перенаправление на каталог, админка и приложение конференций."""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Корневая страница перенаправляет посетителя на каталог конференций.
    path("", RedirectView.as_view(
        pattern_name="conference_list",
        permanent=False
    )),
    path("admin/", admin.site.urls),
    path("conferences/", include("conferences.urls")),
]
