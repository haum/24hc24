# Generated by Django 5.0.2 on 2024-04-04 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serv', '0013_remove_stage_time_limit_stage_end_of_map_submission_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stage',
            name='dev',
            field=models.BooleanField(default=False),
        ),
    ]
