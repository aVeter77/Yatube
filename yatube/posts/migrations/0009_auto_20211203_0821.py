# Generated by Django 2.2.9 on 2021-12-03 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_auto_20211203_0628'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(verbose_name='post text'),
        ),
    ]
