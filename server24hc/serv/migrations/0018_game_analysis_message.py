# Generated by Django 5.0.2 on 2024-04-06 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serv', '0017_team_name_team_position_team_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='analysis_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
