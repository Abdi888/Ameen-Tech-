# Operator bootstrap

This is the operator procedure for the one-time initial tenant. It is not a frozen architecture document, not a deployment runbook, and not a public API.

The command creates three separate outcomes:

1. A platform administrator account with no tenant membership.
2. One retail tenant in status `ACTIVE`.
3. A separate Owner account for that tenant, with the seeded system role Business Owner.

It does not create branches, warehouses, or terminals. It does not copy role templates. It does not grant `platform.*` permissions. Those keys are not in Document 07. Later HTTP calls use the normal session and Document 07 authorization.

Provisioning is a different operation and is not this command. Tenant lifecycle states beyond `ACTIVE`, `SUSPENDED`, and `ARCHIVED` are not implemented.

## Local and development

From `backend/`, after `python manage.py migrate`:

```powershell
$env:AMEEN_BOOTSTRAP_CONFIRM = "bootstrap-initial-tenant"
$env:AMEEN_BOOTSTRAP_PLATFORM_EMAIL = "platform@example.com"
$env:AMEEN_BOOTSTRAP_PLATFORM_PASSWORD = "<at least 12 characters>"
$env:AMEEN_BOOTSTRAP_PLATFORM_FIRST_NAME = "Platform"
$env:AMEEN_BOOTSTRAP_PLATFORM_LAST_NAME = "Admin"
$env:AMEEN_BOOTSTRAP_TENANT_NAME = "Harbor"
$env:AMEEN_BOOTSTRAP_TENANT_SLUG = "harbor"
$env:AMEEN_BOOTSTRAP_TENANT_TIMEZONE = "Africa/Mogadishu"
$env:AMEEN_BOOTSTRAP_TENANT_COUNTRY = "SO"
$env:AMEEN_BOOTSTRAP_OWNER_EMAIL = "owner@example.com"
$env:AMEEN_BOOTSTRAP_OWNER_PASSWORD = "<at least 12 characters>"
$env:AMEEN_BOOTSTRAP_OWNER_FIRST_NAME = "Amina"
$env:AMEEN_BOOTSTRAP_OWNER_LAST_NAME = "Hassan"
python manage.py bootstrap_initial_tenant
Remove-Item Env:AMEEN_BOOTSTRAP_PLATFORM_PASSWORD
Remove-Item Env:AMEEN_BOOTSTRAP_OWNER_PASSWORD
```

`manage.py` uses development settings unless `DJANGO_SETTINGS_MODULE` is set. Timezone defaults to `UTC` when `AMEEN_BOOTSTRAP_TENANT_TIMEZONE` is omitted. Country may be empty.

On an interactive terminal, omit the two password variables and the command prompts without echoing. Do not pass passwords as command arguments.

Do not put these variables in `.env`. Development loads `.env` into the API process. Bootstrap passwords belong only to the one command process.

The command prints the new ids and emails. It does not print passwords. Change both passwords afterward with `POST /api/v1/auth/password/change` once each person can log in. The platform administrator can log in and receives no tenant and no permissions. The Owner logs in to the new tenant.

## One-time guard

The command holds a database lock and writes `bootstrap.completed` in the same transaction as the three identities. A second run, including a run with the same emails and slug, exits with an error and writes nothing. It does not reset passwords and does not create another tenant or Owner.

If the command fails before that commit, the database rolls the attempt back. Fix the reported problem and run it again. An email or slug that already exists is rejected instead of being reused.

## Production policy

Production uses the same command and the same guard. It is still not a public API and it is not a substitute for a future provisioning API.

- Run it once, from a trusted operator shell, with `DJANGO_SETTINGS_MODULE=config.settings.production`.
- There is no signup route, no `/api/v1/bootstrap` route, and no permission key for this command.
- Set the password variables in that process only, then remove them. Do not commit them and do not leave them in the service environment.
- The confirmation value `AMEEN_BOOTSTRAP_CONFIRM=bootstrap-initial-tenant` is required. A process that does not set it exits before writing.
- Do not run the command to add a second tenant, repair a tenant, or provision roles. Those operations are not specified.
- Do not point the command at a database that already completed bootstrap. The guard will refuse the run.
- Platform administrator and Owner stay different people. The platform administrator is not a member of the tenant and is not the Owner.
