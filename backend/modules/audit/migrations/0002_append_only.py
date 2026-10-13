from django.db import migrations

# Document 02: audit rows are append-only for tenant users. The database
# rejects UPDATE and DELETE even when application code bypasses the model.
_FORWARD = """
CREATE OR REPLACE FUNCTION audit.prevent_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs are append-only';
END;
$$;

DROP TRIGGER IF EXISTS audit_logs_append_only ON audit.audit_logs;
CREATE TRIGGER audit_logs_append_only
BEFORE UPDATE OR DELETE ON audit.audit_logs
FOR EACH ROW
EXECUTE FUNCTION audit.prevent_audit_mutation();
"""

_REVERSE = """
DROP TRIGGER IF EXISTS audit_logs_append_only ON audit.audit_logs;
DROP FUNCTION IF EXISTS audit.prevent_audit_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=_FORWARD, reverse_sql=_REVERSE),
    ]
