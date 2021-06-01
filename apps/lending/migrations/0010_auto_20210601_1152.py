# Generated by Django 3.2.3 on 2021-06-01 03:52

from django.db import migrations


def backwards_func(apps, schema_editor):
    """
    Do nothing on reverse.
    """
    pass


def transfer_borrower_data(apps, schema_editor):
    """
    Moves the `borrower` data into `borrower_old` field in Loan model.
    """
    Loan = apps.get_model("lending", "Loan")
    for loan in Loan.objects.all():
        loan.borrower_old = loan.borrower
        loan.save(update_fields=["borrower_old"])


class Migration(migrations.Migration):

    dependencies = [
        ('lending', '0009_loan_borrower_old'),
    ]

    operations = [
        migrations.RunPython(transfer_borrower_data, reverse_code=backwards_func)
    ]