# Generated by Django 3.0.8 on 2020-08-03 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0030_member_transfer_request_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='call_limit',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='calls_sent',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='last_call_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
