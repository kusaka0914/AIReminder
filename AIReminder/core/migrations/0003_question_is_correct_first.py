# Generated by Django 5.1.4 on 2024-12-13 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_customuser_accuracy_customuser_correct_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_correct_first',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
