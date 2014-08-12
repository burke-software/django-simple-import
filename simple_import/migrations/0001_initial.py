# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColumnMatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('column_name', models.CharField(max_length=200)),
                ('field_name', models.CharField(max_length=255, blank=True)),
                ('default_value', models.CharField(max_length=2000, blank=True)),
                ('null_on_empty', models.BooleanField(default=False, help_text=b'If cell is blank, clear out the field setting it to blank.')),
                ('header_position', models.IntegerField(help_text=b'Annoying way to order the columns to match the header rows')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImportedObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.IntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImportLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Date Created')),
                ('import_file', models.FileField(upload_to=b'import_file')),
                ('error_file', models.FileField(upload_to=b'error_file', blank=True)),
                ('import_type', models.CharField(max_length=1, choices=[(b'N', b'Create New Records'), (b'U', b'Create and Update Records'), (b'O', b'Only Update Records')])),
                ('update_key', models.CharField(max_length=200, blank=True)),
                ('user', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='importedobject',
            name='import_log',
            field=models.ForeignKey(to='simple_import.ImportLog'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='ImportSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='importlog',
            name='import_setting',
            field=models.ForeignKey(editable=False, to='simple_import.ImportSetting'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='columnmatch',
            name='import_setting',
            field=models.ForeignKey(to='simple_import.ImportSetting'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='columnmatch',
            unique_together=set([(b'column_name', b'import_setting')]),
        ),
        migrations.AlterUniqueTogether(
            name='importsetting',
            unique_together=set([(b'user', b'content_type')]),
        ),
        migrations.CreateModel(
            name='RelationalMatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=255)),
                ('related_field_name', models.CharField(max_length=255, blank=True)),
                ('import_log', models.ForeignKey(to='simple_import.ImportLog')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
