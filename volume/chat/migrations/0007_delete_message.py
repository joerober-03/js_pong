# Generated by Django 4.2.11 on 2024-04-29 14:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_alter_room_left'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Message',
        ),
    ]