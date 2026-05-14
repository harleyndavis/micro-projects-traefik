from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='link',
            name='qr_scans',
            field=models.IntegerField(default=0),
        ),
    ]
