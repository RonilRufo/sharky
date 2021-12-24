# Generated by Django 3.2.6 on 2021-12-24 04:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_emailuser_is_capital_source_provider'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailuser',
            name='is_borrower_active',
            field=models.BooleanField(default=True, help_text='If the borrower is actively paying or not.'),
        ),
    ]