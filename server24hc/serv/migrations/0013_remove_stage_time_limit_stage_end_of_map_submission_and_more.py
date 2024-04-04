# Generated by Django 5.0.2 on 2024-04-04 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serv', '0012_merge_20240404_0909'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stage',
            name='time_limit',
        ),
        migrations.AddField(
            model_name='stage',
            name='end_of_map_submission',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='stage',
            name='number_of_maps',
            field=models.IntegerField(default=-1),
        ),
    ]
