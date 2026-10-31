from django.contrib import admin
from .models import Conference, Registration, Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Показывает отзывы и их сохранённые даты; даты недоступны для ручной правки."""
    list_display = ("user", "conference", "rating", "conference_start_date", "conference_end_date")
    readonly_fields = ("conference_start_date", "conference_end_date")


admin.site.register(Conference)

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """Позволяет администратору искать заявки и менять рекомендации к публикации."""
    list_display = (
        "presentation_title",
        "user",
        "conference",
        "recommended"
    )
    list_filter = ("recommended", "conference")
    search_fields = ("presentation_title", "user__username")
    list_editable = ("recommended",)
