from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notices', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notice',
            name='expires_at',
            field=models.DateField(blank=True, null=True),
        ),
    ]
