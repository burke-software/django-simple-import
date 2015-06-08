# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ColumnMatch',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('column_name', models.CharField(max_length=200)),
                ('field_name', models.CharField(blank=True, max_length=255)),
                ('default_value', models.CharField(blank=True, max_length=2000)),
                ('null_on_empty', models.BooleanField(default=False, help_text='If cell is blank, clear out the field setting it to blank.')),
                ('header_position', models.IntegerField(help_text='Annoying way to order the columns to match the header rows')),
            ],
        ),
        migrations.CreateModel(
            name='ImportedObject',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('object_id', models.IntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ImportLog',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('import_file', models.FileField(upload_to='import_file')),
                ('error_file', models.FileField(blank=True, upload_to='error_file')),
                ('import_type', models.CharField(choices=[('N', 'Create New Records'), ('U', 'Create and Update Records'), ('O', 'Only Update Records')], max_length=1)),
                ('update_key', models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ImportSetting',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RelationalMatch',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=255)),
                ('related_field_name', models.CharField(blank=True, max_length=255)),
                ('import_log', models.ForeignKey(to='simple_import.ImportLog')),
            ],
        ),
        migrations.AddField(
            model_name='importlog',
            name='import_setting',
            field=models.ForeignKey(to='simple_import.ImportSetting', editable=False),
        ),
        migrations.AddField(
            model_name='importlog',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='simple_import_log', editable=False),
        ),
        migrations.AddField(
            model_name='importedobject',
            name='import_log',
            field=models.ForeignKey(to='simple_import.ImportLog'),
        ),
        migrations.AddField(
            model_name='columnmatch',
            name='import_setting',
            field=models.ForeignKey(to='simple_import.ImportSetting'),
        ),
        migrations.AlterUniqueTogether(
            name='importsetting',
            unique_together=set([('user', 'content_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='columnmatch',
            unique_together=set([('column_name', 'import_setting')]),
        ),
    ]
