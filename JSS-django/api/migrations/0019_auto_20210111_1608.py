# Generated by Django 3.0 on 2021-01-11 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_resource_download'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='source',
            field=models.CharField(blank=True, max_length=1024, null=True, verbose_name='来源'),
        ),
    ]