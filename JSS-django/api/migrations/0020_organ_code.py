# Generated by Django 3.0 on 2021-03-09 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_auto_20210111_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='organ',
            name='code',
            field=models.CharField(blank=True, max_length=6, verbose_name='邀请码'),
        ),
    ]