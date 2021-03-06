# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-13 13:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('decisions', '0005_imported_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='action',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='case',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='case',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='casegeometry',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='casegeometry',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='content',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='content',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='datasource',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='datasource',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='event',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='event',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='eventattendee',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='eventattendee',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='function',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='function',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='importedfile',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='importedfile',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='person',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='person',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
        migrations.AlterField(
            model_name='post',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was created'),
        ),
        migrations.AlterField(
            model_name='post',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='The time at which the resource was updated'),
        ),
    ]
