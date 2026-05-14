from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0002_link_qr_scans'),
    ]

    operations = [
        migrations.AlterField(
            model_name='link',
            name='original_url',
            field=models.URLField(max_length=2000, unique=True),
        ),
    ]
