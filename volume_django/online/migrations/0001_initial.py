# Generated by Django 4.2.13 on 2024-05-13 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_name', models.CharField(max_length=255)),
                ('full', models.BooleanField(default=False)),
                ('quickmatch', models.BooleanField(default=False)),
            ],
        ),
    ]
