from django.db import migrations, models


def fill_conference_dates(apps, schema_editor):
    """Заполняет даты старых отзывов текущими датами связанных конференций."""
    Conference = apps.get_model('conferences', 'Conference')
    Review = apps.get_model('conferences', 'Review')
    alias = schema_editor.connection.alias
    # Старые даты неизвестны: для прежних отзывов сохраняем текущий период.
    for conference in Conference.objects.using(alias).all().iterator():
        Review.objects.using(alias).filter(conference_id=conference.pk).update(
            conference_start_date=conference.start_date,
            conference_end_date=conference.end_date,
        )


class Migration(migrations.Migration):
    dependencies = [('conferences', '0004_review')]

    operations = [
        migrations.AddField(
            model_name='review', name='conference_start_date',
            field=models.DateField('Дата начала конференции', editable=False, null=True),
        ),
        migrations.AddField(
            model_name='review', name='conference_end_date',
            field=models.DateField('Дата окончания конференции', editable=False, null=True),
        ),
        migrations.RunPython(fill_conference_dates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='review', name='conference_start_date',
            field=models.DateField('Дата начала конференции', editable=False),
        ),
        migrations.AlterField(
            model_name='review', name='conference_end_date',
            field=models.DateField('Дата окончания конференции', editable=False),
        ),
    ]
