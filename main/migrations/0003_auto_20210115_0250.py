# Generated by Django 3.1.5 on 2021-01-14 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20210115_0246'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connection',
            name='users',
            field=models.ManyToManyField(related_name='connection_between', to='main.UserAccount'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='sent_to',
            field=models.ManyToManyField(related_name='notification_to', to='main.UserAccount'),
        ),
    ]
