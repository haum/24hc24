# Generated by Django 5.0.2 on 2024-04-04 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serv', '0014_stage_dev'),
    ]

    operations = [
        migrations.AddField(
            model_name='map',
            name='impossible',
            field=models.BooleanField(default=False),
        ),
    ]
