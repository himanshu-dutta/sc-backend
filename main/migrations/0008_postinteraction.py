# Generated by Django 3.1.5 on 2021-01-25 19:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_auto_20210125_2113'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostInteraction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('like', models.BooleanField(default=False)),
                ('report', models.BooleanField(default=False)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.useraccount')),
            ],
        ),
    ]
