# Generated by Django 5.1.3 on 2025-01-09 11:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prof', '0005_alter_userprofile_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='email',
        ),
    ]
