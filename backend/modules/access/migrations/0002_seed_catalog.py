from django.db import migrations

from modules.access.infrastructure.seed import sync_historical_catalog


def seed(apps: object, schema_editor: object) -> None:
    del schema_editor
    sync_historical_catalog(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
