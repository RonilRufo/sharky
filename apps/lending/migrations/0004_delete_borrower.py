# Generated by Django 3.2.6 on 2021-08-26 04:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lending', '0003_remove_loan_borrower_old'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Borrower',
        ),
    ]
