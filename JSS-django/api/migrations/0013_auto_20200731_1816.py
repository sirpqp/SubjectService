# Generated by Django 3.0.4 on 2020-07-31 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_auto_20200728_2227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='attachment',
            field=models.FileField(blank=True, max_length=2550, upload_to='uploads/res/%Y/%m/%d/', verbose_name='文件路径'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='source',
            field=models.CharField(blank=True, max_length=1024, verbose_name='来源'),
        ),
    ]