# Generated by Django 3.2.3 on 2021-05-15 10:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lending', '0003_auto_20210515_1430'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loansource',
            name='loan',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='source', to='lending.loan'),
        ),
    ]
