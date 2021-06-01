# Generated by Django 3.2.3 on 2021-06-01 03:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lending', '0008_alter_bank_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='loan',
            name='borrower_old',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='legacy_loans', to='lending.borrower'),
        ),
    ]
