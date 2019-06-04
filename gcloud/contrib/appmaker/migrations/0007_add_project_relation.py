# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-05-17 08:32
from __future__ import unicode_literals

from django.db import migrations


def reverse_func(apps, schema_editor):
    AppMaker = apps.get_model('appmaker', 'AppMaker')
    db_alias = schema_editor.connection.alias
    AppMaker.objects.using(db_alias).all().update(project=None)


def forward_func(apps, schema_editor):
    AppMaker = apps.get_model('appmaker', 'AppMaker')
    Business = apps.get_model('core', 'Business')

    cc_ids = Business.objects.all().values_list('cc_id', flat=True)

    for cc_id in cc_ids:
        AppMaker.objects.filter(business__cc_id=cc_id).update(project_id=cc_id)


class Migration(migrations.Migration):
    dependencies = [
        ('appmaker', '0006_appmaker_project'),
        ('core', '0010_create_project_for_exist_biz'),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func)
    ]