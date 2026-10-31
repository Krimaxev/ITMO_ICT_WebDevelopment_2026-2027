from datetime import date
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from .models import Conference, Registration, Review


class ConferenceTests(TestCase):
    """Проверки пользовательских сценариев, прав доступа, форм и страниц приложения."""
    @classmethod
    def setUpTestData(cls):
        """Создаёт общие данные сценариев: двух пользователей, сотрудника, конференцию и заявку."""
        users = get_user_model()
        cls.owner = users.objects.create_user('owner', password='test-password')
        cls.other = users.objects.create_user('other', password='test-password')
        cls.staff = users.objects.create_user('staff', is_staff=True)
        cls.conference = Conference.objects.create(title='Science', location='SPb', start_date=date(2026,10,1), end_date=date(2026,10,2), topic='Physics, Mathematics', description='Conference description', venue_description='Venue description', participation_terms='Participation terms')
        cls.application = Registration.objects.create(conference=cls.conference, user=cls.owner, presentation_title='Talk', description='Abstract')

    def test_anonymous_apply_redirects_to_real_login(self):
        """Гость перенаправляется на существующий маршрут входа."""
        url = reverse('apply_to_conference', args=[self.conference.pk])
        self.assertRedirects(self.client.get(url), reverse('login') + '?next=' + url)

    def test_other_user_cannot_edit_or_delete(self):
        """Чужая заявка недоступна для изменения и удаления даже по прямому URL."""
        self.client.force_login(self.other)
        for name in ('edit_application', 'delete_application'):
            url = reverse(name, args=[self.application.pk])
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url, {'presentation_title':'Hacked','description':'x'}).status_code, 404)
        self.application.refresh_from_db()
        self.assertEqual(self.application.presentation_title, 'Talk')

    def test_owner_can_edit_but_cannot_set_privileged_fields(self):
        """Владелец редактирует доклад, но не может подменить автора или результат."""
        self.client.force_login(self.owner)
        response = self.client.post(reverse('edit_application',args=[self.application.pk]), {'presentation_title':'Updated','description':'New abstract','recommended':'on','user':self.other.pk})
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.presentation_title, 'Updated')
        self.assertEqual(self.application.user_id, self.owner.pk)
        self.assertFalse(self.application.recommended)

    def test_delete_requires_post(self):
        """Просмотр подтверждения безопасен; запись удаляется только POST-запросом."""
        self.client.force_login(self.owner)
        url = reverse('delete_application',args=[self.application.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Registration.objects.filter(pk=self.application.pk).exists())
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Registration.objects.filter(pk=self.application.pk).exists())

    def test_new_application_uses_logged_in_user(self):
        """Автор новой заявки берётся из сессии, а не из присланных полей."""
        self.client.force_login(self.other)
        response=self.client.post(reverse('apply_to_conference',args=[self.conference.pk]),{'presentation_title':'New talk','description':'Abstract','user':self.owner.pk,'recommended':'on'})
        self.assertEqual(response.status_code,302)
        application=Registration.objects.get(presentation_title='New talk')
        self.assertEqual(application.user_id,self.other.pk)
        self.assertFalse(application.recommended)

    def test_review_rating_boundaries(self):
        """Оценки 1 и 10 допустимы, значения за этими пределами отклоняются."""
        self.client.force_login(self.owner)
        url=reverse('add_review',args=[self.conference.pk])
        for rating in (0,11):
            self.assertEqual(self.client.post(url,{'text':'Review','rating':rating}).status_code,200)
        self.assertEqual(Review.objects.count(),0)
        for rating in (1,10):
            self.assertEqual(self.client.post(url,{'text':'Review','rating':rating}).status_code,302)
        self.assertEqual(Review.objects.filter(user=self.owner).count(),2)

    def test_registration_and_login_logout(self):
        """Регистрация создаёт сессию; выход и повторный вход работают."""
        response=self.client.post(reverse('register'),{'username':'newuser','password1':'Strong-example-42','password2':'Strong-example-42'})
        self.assertEqual(response.status_code,302)
        self.assertIn('_auth_user_id',self.client.session)
        self.assertEqual(self.client.post(reverse('logout')).status_code,302)
        self.assertNotIn('_auth_user_id',self.client.session)
        self.assertEqual(self.client.post(reverse('login'),{'username':'newuser','password':'Strong-example-42'}).status_code,302)

    def test_detail_displays_required_descriptions(self):
        """Страница конференции выводит все описательные поля варианта №5."""
        response=self.client.get(reverse('conference_detail',args=[self.conference.pk]))
        for text in ('Physics, Mathematics','Conference description','Venue description','Participation terms'):
            self.assertContains(response,text)

    def test_catalog_pagination_and_search(self):
        """Пагинация применяется к найденным конференциям и сохраняет поисковый запрос."""
        for i in range(12):
            Conference.objects.create(title=f'Match {i}',location='Moscow',start_date=date(2026,11,1),end_date=date(2026,11,2))
        response=self.client.get(reverse('conference_list'),{'q':'Match','page':2})
        self.assertEqual(response.context['page_obj'].paginator.count,12)
        self.assertEqual(len(response.context['conferences']),2)
        self.assertContains(response,'q=Match')

    def test_all_participants_table(self):
        """Общая таблица содержит конференцию, имя автора и название доклада."""
        response=self.client.get(reverse('participant_list'))
        for text in ('<table','owner','Science','Talk'):
            self.assertContains(response,text)

    def test_moderation_is_staff_only_and_post_only(self):
        """Модерация проверяет роль, HTTP-метод и значение результата на сервере."""
        url=reverse('set_recommendation',args=[self.application.pk])
        self.assertEqual(self.client.post(url,{'recommended':'true'}).status_code,302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url,{'recommended':'true'}).status_code,403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code,405)
        self.assertEqual(self.client.post(url,{'recommended':'invalid'}).status_code,400)
        for value in ('true','false'):
            self.assertEqual(self.client.post(url,{'recommended':value}).status_code,302)
            self.application.refresh_from_db()
            self.assertEqual(self.application.recommended,value=='true')

    def test_moderation_controls_visible_only_to_staff(self):
        """Обычный пользователь не видит кнопки изменения результата."""
        url=reverse('conference_detail',args=[self.conference.pk])
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(url),'Рекомендовать к публикации')
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(url),'Рекомендовать к публикации')

    def test_csrf_required_for_mutations(self):
        """Изменяющие запросы без CSRF-токена отклоняются."""
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(reverse('delete_application',args=[self.application.pk])).status_code,403)
        client.force_login(self.staff)
        self.assertEqual(client.post(reverse('set_recommendation',args=[self.application.pk]),{'recommended':'true'}).status_code,403)

    def test_review_copies_dates_on_creation_and_ignores_posted_dates(self):
        """Даты отзыва копируются из конференции; подмена полей в POST не действует."""
        self.client.force_login(self.owner)
        response = self.client.post(reverse('add_review', args=[self.conference.pk]), {
            'text': 'Date snapshot', 'rating': 8,
            'conference_start_date': '2000-01-01', 'conference_end_date': '2000-01-02',
        })
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(text='Date snapshot')
        self.assertEqual(review.conference_start_date, date(2026, 10, 1))
        self.assertEqual(review.conference_end_date, date(2026, 10, 2))

    def test_review_keeps_dates_after_conference_and_text_change(self):
        """Перенос конференции и правка текста не меняют сохранённые даты отзыва."""
        review = Review.objects.create(conference=self.conference, user=self.owner, text='Before move', rating=8)
        self.conference.start_date = date(2026, 12, 1)
        self.conference.end_date = date(2026, 12, 2)
        self.conference.save()
        review.text = 'After move'
        review.save()
        review.refresh_from_db()
        self.assertEqual(review.conference_start_date, date(2026, 10, 1))
        self.assertEqual(review.conference_end_date, date(2026, 10, 2))
        response = self.client.get(reverse('conference_detail', args=[self.conference.pk]))
        self.assertContains(response, '01.10.2026')
        self.assertContains(response, '02.10.2026')

    def test_new_review_uses_rescheduled_conference_dates(self):
        """Отзыв после переноса получает новый период проведения конференции."""
        self.conference.start_date = date(2026, 12, 1)
        self.conference.end_date = date(2026, 12, 2)
        self.conference.save()
        review = Review.objects.create(conference=self.conference, user=self.owner, text='After move', rating=9)
        self.assertEqual(review.conference_start_date, date(2026, 12, 1))
        self.assertEqual(review.conference_end_date, date(2026, 12, 2))


class ReviewDatesMigrationTests(TransactionTestCase):
    """Проверка переноса существующих отзывов со старой схемы на новую."""
    def test_existing_review_is_backfilled_without_losing_content(self):
        """Миграция заполняет даты старого отзыва и сохраняет его содержимое."""
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        before = [('conferences', '0004_review')]
        after = [('conferences', '0005_review_conference_dates')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        try:
            apps = executor.loader.project_state(before).apps
            user = apps.get_model('auth', 'User').objects.create(username='historical')
            conference = apps.get_model('conferences', 'Conference').objects.create(
                title='Historical', location='SPb', start_date=date(2026, 10, 1), end_date=date(2026, 10, 2),
            )
            old_review = apps.get_model('conferences', 'Review').objects.create(
                user_id=user.pk, conference_id=conference.pk, text='Keep this text', rating=7,
            )
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            review = Review.objects.get(pk=old_review.pk)
            self.assertEqual(review.text, 'Keep this text')
            self.assertEqual(review.rating, 7)
            self.assertEqual(review.user_id, user.pk)
            self.assertEqual(review.conference_start_date, date(2026, 10, 1))
            self.assertEqual(review.conference_end_date, date(2026, 10, 2))
        finally:
            MigrationExecutor(connection).migrate(after)
