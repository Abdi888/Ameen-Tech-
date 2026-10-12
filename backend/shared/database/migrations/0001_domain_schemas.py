"""Create the PostgreSQL schemas named in Document 00 §1.

Document 02 also says "shared schema". Document 00 wins, so each domain has its
own schema. This migration does not create tables; later phases add those with
their modules.
"""

from django.db import migrations

# Names are fixed architecture identifiers, not request input.
DOMAIN_SCHEMAS = (
    "identity",
    "organization",
    "catalog",
    "inventory",
    "sales",
    "purchasing",
    "customers",
    "suppliers",
    "payments",
    "expenses",
    "accounting",
    "tax",
    "audit",
    "system",
)

_CREATE = "\n".join(f"CREATE SCHEMA IF NOT EXISTS {name};" for name in DOMAIN_SCHEMAS)
_DROP = "\n".join(f"DROP SCHEMA IF EXISTS {name};" for name in DOMAIN_SCHEMAS)


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(sql=_CREATE, reverse_sql=_DROP),
    ]
