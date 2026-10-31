from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Registration
from .models import Registration, Review

class RegisterForm(UserCreationForm):
    """Стандартная регистрация Django с проверкой имени и двух введённых паролей."""
    pass

class RegistrationForm(forms.ModelForm):
    """Форма заявки: пользователь вводит только название и описание доклада."""
    class Meta:
        """Определяет модель и явный список полей, доступных через форму."""
        model = Registration
        # Автор, конференция и рекомендация исключены из пользовательского ввода.
        fields = ["presentation_title", "description"]

class ReviewForm(forms.ModelForm):
    """Форма отзыва: текст и оценка; автор и даты задаются приложением."""
    class Meta:
        """Определяет модель и явный список полей, доступных через форму."""
        model = Review
        # ModelForm применяет валидаторы модели, в том числе диапазон рейтинга 1–10.
        fields = ["text", "rating"]