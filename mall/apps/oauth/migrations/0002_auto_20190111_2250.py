# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-01-11 14:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oauthqquser',
            name='openid',
            field=models.CharField(db_index=True, max_length=64, unique=True, verbose_name='openid'),
        ),
    ]