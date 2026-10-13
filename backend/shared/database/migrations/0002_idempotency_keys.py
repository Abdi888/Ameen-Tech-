"""Create system.idempotency_keys.

Document 02 columns: tenant_id, key, endpoint, response, created_at, with
UNIQUE(tenant_id, key). The UUID primary key follows Document 02's ID rule.
Document 02 does not set a length for key or endpoint, so both are text.

Not created in this phase:
- outbox: Document 00 requires a row inside CompleteSale, and Document 02
  does not define the table. Its columns stay unresolved.
- tenant_settings, documents, and document_sequences.
- currencies, and the foreign key from tenants.default_currency_id.
"""

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ameen_database", "0001_domain_schemas"),
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="IdempotencyKey",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("key", models.TextField()),
                ("endpoint", models.TextField()),
                ("response", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="idempotency_keys",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={
                "db_table": '"system"."idempotency_keys"',
                "constraints": [
                    models.UniqueConstraint(
                        fields=("tenant", "key"),
                        name="idempotency_tenant_key",
                    )
                ],
            },
        ),
    ]
