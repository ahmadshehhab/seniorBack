# Generated by Django 4.2.17 on 2025-01-09 20:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prof", "0012_posts_price_alter_userprofile_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="posts",
            name="status",
            field=models.BooleanField(
                choices=[(True, "Active"), (False, "Inactive")], default=False
            ),
        ),
    ]
