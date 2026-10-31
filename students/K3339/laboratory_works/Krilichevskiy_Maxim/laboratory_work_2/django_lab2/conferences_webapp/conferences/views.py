from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.http import HttpResponse
from .models import Conference
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from django.shortcuts import redirect
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .forms import RegistrationForm
from .models import Conference, Registration
from .models import Review
from .forms import ReviewForm
from django.db.models import Q


def conference_list(request):
    """Показывает каталог: поиск по трём полям и страницы по 10 конференций."""
    query = request.GET.get("q", "").strip()

    # Дополнительная сортировка по pk делает порядок страниц стабильным при одинаковых датах.
    conferences = Conference.objects.all().order_by("start_date", "pk")

    # Q с оператором | означает: совпадение хотя бы в одном из полей.
    if query:
        conferences = conferences.filter(
            Q(title__icontains=query) |
            Q(topic__icontains=query) |
            Q(location__icontains=query)
        )

    # get_page обрабатывает пустой, некорректный и выходящий за диапазон номер страницы.
    page_obj = Paginator(conferences, 10).get_page(request.GET.get("page"))
    return render(request, "conferences/conference_list.html", {
        "conferences": page_obj,
        "page_obj": page_obj,
        "query": query,
    })


def conference_detail(request, conference_id):
    """Собирает сведения о конференции, личные заявки, участников и отзывы."""
    conference = get_object_or_404(Conference, id=conference_id)

    # Личные заявки текущего пользователя
    if request.user.is_authenticated:
        applications = Registration.objects.filter(
            conference=conference,
            user=request.user
        )
    else:
        applications = Registration.objects.none()

    # Все участники конференции
    # Связанный пользователь загружается тем же запросом, без запроса на каждую строку.
    participants = Registration.objects.filter(conference=conference).select_related("user")

    # Отзывы о конференции
    reviews = Review.objects.filter(conference=conference).select_related("user").order_by("-created_at")

    return render(request, "conferences/conference_detail.html", {
        "conference": conference,
        "applications": applications,
        "reviews": reviews,
        "participants": participants,
    })



def register(request):
    """На GET показывает форму; на корректный POST создаёт пользователя и выполняет вход."""
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("conference_list")
    else:
        form = RegisterForm()

    return render(request, "conferences/register.html", {"form": form})


@login_required
def apply_to_conference(request, conference_id):
    """Создаёт заявку от текущего пользователя на конференцию из URL."""
    conference = get_object_or_404(Conference, id=conference_id)

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            # Пока не пишем в БД: сначала проставляем автора и конференцию на сервере.
            application = form.save(commit=False)
            application.user = request.user
            application.conference = conference
            application.save()

            return redirect("conference_detail", conference_id=conference.id)
    else:
        form = RegistrationForm()

    return render(request, "conferences/apply.html", {"form": form, "conference": conference})


@login_required
def edit_application(request, application_id):
    """Показывает и сохраняет форму изменения только собственной заявки."""
    # Фильтр по автору защищает запись независимо от наличия кнопок в шаблоне.
    application = get_object_or_404(Registration, id=application_id, user=request.user)

    if request.method == "POST":
        form = RegistrationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            return redirect("conference_detail", conference_id=application.conference_id)
    else:
        form = RegistrationForm(instance=application)

    return render(request, "conferences/apply.html", {"form": form, "conference": application.conference})


@login_required
def delete_application(request, application_id):
    """На GET просит подтверждение; на POST удаляет только собственную заявку."""
    # Фильтр по автору защищает запись независимо от наличия кнопок в шаблоне.
    application = get_object_or_404(Registration, id=application_id, user=request.user)

    if request.method == "POST":
        conference_id = application.conference_id
        application.delete()
        return redirect("conference_detail", conference_id=conference_id)

    return render(request, "conferences/delete_application.html", { "application": application})


@login_required
def add_review(request, conference_id):
    """Проверяет форму и сохраняет отзыв с автором и снимком дат конференции."""
    conference = get_object_or_404(Conference, id=conference_id)

    if request.method == "POST":
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.conference = conference
            # Review.save() автоматически сохраняет период конференции вместе с отзывом.
            review.save()

            return redirect(
                "conference_detail",
                conference_id=conference.id
            )
    else:
        form = ReviewForm()

    return render(request, "conferences/add_review.html", {"form": form, "conference": conference})


def participant_list(request):
    """Выводит общую таблицу выступлений с группировкой порядком по конференциям."""
    participants = Registration.objects.select_related("user", "conference").order_by("conference__start_date", "conference_id", "user__username", "pk")
    return render(request, "conferences/participant_list.html", {"participants": participants})


@login_required
@require_POST
def set_recommendation(request, application_id):
    """Меняет результат выступления по POST, доступен только staff/superuser."""
    # Скрыть кнопку недостаточно: прямой POST обычного пользователя тоже запрещён.
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied
    application = get_object_or_404(Registration, pk=application_id)
    # Разбираем только два допустимых значения; bool("false") дал бы True.
    value = request.POST.get("recommended")
    if value not in ("true", "false"):
        return HttpResponseBadRequest("Некорректный результат выступления")
    application.recommended = value == "true"
    application.save(update_fields=["recommended"])
    return redirect("conference_detail", conference_id=application.conference_id)
