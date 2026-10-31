from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Conference(models.Model):
    """Конференция: название, место, период, тематики, описание и условия участия."""
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()

    venue_description = models.TextField(blank=True, default="")
    
    # Несколько тематик вводятся текстом, например через запятую.
    topic = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField(blank=True, default="")
    participation_terms = models.TextField(blank=True, default="")

    def __str__(self):
        """Возвращает название конференции для админки и текстового вывода."""
        return self.title


class Registration(models.Model):
    """Заявка автора на выступление; связывает пользователя с конференцией."""
    # Ссылка на активную модель пользователя из настроек Django.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name="registrations")
    presentation_title = models.CharField(max_length=200)
    description = models.TextField()
    # False означает «не рекомендован», True — «рекомендован к публикации».
    recommended = models.BooleanField(default=False)

    def __str__(self):
        """Возвращает название доклада для выбора и отображения заявки."""
        return self.presentation_title


class Review(models.Model):
    """Отзыв об одной конференции с оценкой и сохранённым периодом её проведения."""
    conference = models.ForeignKey(
        Conference,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ]
    )
    # Эти поля не входят в пользовательскую форму и заполняются автоматически.
    conference_start_date = models.DateField("Дата начала конференции", editable=False)
    conference_end_date = models.DateField("Дата окончания конференции", editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Снимок периода сохраняется при создании и не меняется при переносе конференции.
        """При первом сохранении копирует даты конференции; при правке отзыва оставляет их прежними."""
        if self._state.adding:
            self.conference_start_date = self.conference.start_date
            self.conference_end_date = self.conference.end_date
        super().save(*args, **kwargs)


    def __str__(self):
        """Возвращает автора, конференцию и оценку для отображения отзыва."""
        return f"{self.user} — {self.conference} ({self.rating}/10)"