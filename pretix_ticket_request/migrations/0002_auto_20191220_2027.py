# Generated by Django 2.2.7 on 2019-12-20 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pretix_ticket_request', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketrequest',
            name='status',
            field=models.CharField(db_index=True, default='pending', max_length=10),
        ),
    ]
