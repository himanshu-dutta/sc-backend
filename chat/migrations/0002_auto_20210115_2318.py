# Generated by Django 3.1.5 on 2021-01-15 17:48

import chat.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='media',
            field=models.FileField(blank=True, null=True, upload_to=chat.models.get_media_path),
        ),
    ]
