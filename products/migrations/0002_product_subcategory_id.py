from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='subcategory_id',
            field=models.UUIDField(blank=True, null=True),
        ),
    ]
