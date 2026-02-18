"""
Realign Django model definitions with the pre-existing Supabase table schema.
Tables already exist with the correct columns — this is a state-only migration.
"""
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            sql=migrations.RunSQL.noop,
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[
                migrations.DeleteModel('CurrencyRate'),
                migrations.DeleteModel('UserCurrencyPreference'),
                migrations.CreateModel(
                    name='CurrencyRate',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('from_currency', models.TextField()),
                        ('to_currency', models.TextField()),
                        ('rate', models.DecimalField(decimal_places=6, max_digits=20)),
                        ('source', models.TextField(default='manual')),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                    ],
                    options={
                        'db_table': 'currency_rates',
                        'managed': False,
                    },
                ),
                migrations.CreateModel(
                    name='UserCurrencyPreference',
                    fields=[
                        ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ('preferred_currency', models.TextField(default='NGN')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='currency_preference', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'user_currency_preferences',
                        'managed': False,
                    },
                ),
            ],
        ),
    ]
