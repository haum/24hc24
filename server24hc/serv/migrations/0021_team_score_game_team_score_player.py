# Generated by Django 5.0.2 on 2024-04-07 05:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serv', '0020_alter_stage_maps'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='score_game',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='team',
            name='score_player',
            field=models.FloatField(default=0),
        ),
    ]
