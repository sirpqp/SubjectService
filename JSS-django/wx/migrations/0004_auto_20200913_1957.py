# Generated by Django 3.0.4 on 2020-09-13 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wx', '0003_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auth',
            name='openid',
            field=models.CharField(max_length=28, unique=True, verbose_name='微信用户ID'),
        ),
        migrations.AlterField(
            model_name='location',
            name='latitude',
            field=models.FloatField(verbose_name='授权地纬度'),
        ),
        migrations.AlterField(
            model_name='location',
            name='longitude',
            field=models.FloatField(verbose_name='授权地经度'),
        ),
        migrations.AlterField(
            model_name='location',
            name='openid',
            field=models.CharField(max_length=28, unique=True, verbose_name='微信用户ID'),
        ),
    ]
