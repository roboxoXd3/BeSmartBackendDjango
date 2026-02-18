from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_add_shipping_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='squad_gateway_ref',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
