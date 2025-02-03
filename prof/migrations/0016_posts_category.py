# Generated by Django 4.2.17 on 2025-01-11 10:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("prof", "0015_postscategory"),
    ]

    operations = [
        migrations.AddField(
            model_name="posts",
            name="category",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="post_category",
                to="prof.postscategory",
            ),
        ),
    ]
