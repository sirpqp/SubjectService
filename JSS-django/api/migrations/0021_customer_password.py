# Generated by Django 2.1.15 on 2021-04-11 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0020_organ_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='password',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='密码'),
        ),
    ]
