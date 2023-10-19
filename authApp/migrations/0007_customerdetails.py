# Generated by Django 4.1.4 on 2023-10-17 23:06

import cloudinary_storage.storage
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authApp', '0006_otpmodel_otp_expire'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=255, null=True)),
                ('last_name', models.CharField(max_length=255, null=True)),
                ('phone_number', models.CharField(max_length=255, null=True)),
                ('address', models.CharField(max_length=255, null=True)),
                ('city', models.CharField(max_length=70, null=True)),
                ('state', models.CharField(max_length=100, null=True)),
                ('zipcode', models.IntegerField(null=True)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('nin', models.IntegerField(null=True)),
                ('fpage', models.ImageField(blank=True, null=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(), upload_to='images/')),
                ('bpage', models.ImageField(blank=True, null=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(), upload_to='images/')),
                ('security_question', models.CharField(max_length=255, null=True)),
                ('security_answer', models.CharField(max_length=255, null=True)),
                ('picture', models.ImageField(blank=True, null=True, storage=cloudinary_storage.storage.RawMediaCloudinaryStorage(), upload_to='images/')),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Customer Details',
            },
        ),
    ]
