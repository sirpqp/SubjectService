# Generated by Django 3.0.4 on 2020-07-28 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_auto_20200728_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='short',
            field=models.CharField(default='SoWt70', max_length=6, verbose_name='短地址'),
        ),
    ]
