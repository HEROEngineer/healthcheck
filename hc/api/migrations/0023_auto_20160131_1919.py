# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-31 19:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("api", "0022_auto_20160130_2042")]

    operations = [
        migrations.AlterModelOptions(
            name="notification", options={"get_latest_by": "created"}
        )
    ]
