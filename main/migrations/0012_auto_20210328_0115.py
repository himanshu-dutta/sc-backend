# Generated by Django 3.1.5 on 2021-03-27 19:45

from django.db import migrations
import django_resized.forms
import main.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_auto_20210207_0343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraccount',
            name='display_picture',
            field=django_resized.forms.ResizedImageField(blank=True, crop=None, default='/app/static/images/default_dp.png', force_format=None, keep_meta=True, quality=100, size=[300, 300], upload_to=main.models.get_dp_path),
        ),
    ]
