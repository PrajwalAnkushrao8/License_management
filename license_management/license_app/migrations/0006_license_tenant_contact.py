# Generated by Django 4.2.6 on 2024-07-29 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('license_app', '0005_license_license_provided_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='license',
            name='tenant_contact',
            field=models.CharField(default='Please Update the Contact details', max_length=255),
        ),
    ]
