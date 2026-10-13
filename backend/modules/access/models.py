"""Roles, permissions, and membership. Document 00 has no separate access schema."""

from __future__ import annotations

from django.db import models

from shared.database.models import TimestampedModel, UuidModel


class Permission(UuidModel):
    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=80)
    module = models.CharField(max_length=80)
    description = models.TextField(blank=True, default="")
    is_system = models.BooleanField(default=True)
    danger_level = models.CharField(max_length=16)

    class Meta:
        db_table = '"identity"."permissions"'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(danger_level__in=["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                name="permissions_danger_known",
            ),
        ]


class Role(TimestampedModel):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="roles",
    )
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True, default="")
    is_system_role = models.BooleanField(default=False)

    class Meta:
        db_table = '"identity"."roles"'
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(tenant__isnull=True),
                name="roles_system_name_unique",
            ),
            models.UniqueConstraint(
                fields=["tenant", "name"],
                condition=models.Q(tenant__isnull=False),
                name="roles_tenant_name_unique",
            ),
        ]


class RolePermission(models.Model):
    pk = models.CompositePrimaryKey("role", "permission")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="grants")
    permission = models.ForeignKey(Permission, on_delete=models.PROTECT, related_name="grants")

    class Meta:
        db_table = '"identity"."role_permissions"'


class TenantMembership(TimestampedModel):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    user = models.ForeignKey(
        "identity.User",
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    status = models.CharField(max_length=32)
    is_owner = models.BooleanField(default=False)
    joined_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = '"identity"."tenant_memberships"'
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "user"],
                name="membership_tenant_user",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["ACTIVE", "INVITED", "SUSPENDED", "REMOVED"]),
                name="membership_status",
            ),
        ]


class TenantUserRole(UuidModel):
    membership = models.ForeignKey(
        TenantMembership,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="assignments")
    branch_id = models.UUIDField(null=True, blank=True)
    applies_to_all_branches = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = '"identity"."tenant_user_roles"'
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "role"],
                condition=models.Q(applies_to_all_branches=True),
                name="user_role_all_branches",
            ),
            models.UniqueConstraint(
                fields=["membership", "role", "branch_id"],
                condition=models.Q(branch_id__isnull=False),
                name="user_role_one_branch",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(applies_to_all_branches=True, branch_id__isnull=True)
                    | models.Q(applies_to_all_branches=False, branch_id__isnull=False)
                ),
                name="user_role_branch_scope",
            ),
        ]
