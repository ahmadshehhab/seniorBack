# Generated by Django 5.1.3 on 2025-01-09 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prof', '0003_userprofile_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='email',
            field=models.CharField(default='a@a.com', max_length=255, unique=True),
        ),
    ]
