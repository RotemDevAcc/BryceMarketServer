# Generated by Django 4.2.6 on 2023-12-31 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_coupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='code',
            field=models.CharField(max_length=150, null=True),
        ),
    ]
