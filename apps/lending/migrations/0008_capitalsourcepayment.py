# Generated by Django 3.2.6 on 2021-08-31 03:16

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lending', '0007_remove_capitalsource_from_third_party'),
    ]

    operations = [
        migrations.CreateModel(
            name='CapitalSourcePayment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=9)),
                ('due_date', models.DateField()),
                ('paid_date', models.DateField(blank=True, null=True)),
                ('loan_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='capital_source_payments', to='lending.loansource')),
            ],
            options={
                'verbose_name': 'Capital Source Payment',
                'verbose_name_plural': 'Capital Source Payments',
                'ordering': ('due_date',),
            },
        ),
    ]
