from __future__ import annotations

import uuid

from rest_framework import serializers

from modules.identity.api.serializers import StrictSerializer


class InviteSerializer(StrictSerializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    role_id = serializers.UUIDField()


class UserUpdateSerializer(StrictSerializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)


class RoleAssignmentSerializer(StrictSerializer):
    role_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)

    def validate_role_ids(self, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) > 8:
            raise serializers.ValidationError("Too many roles.")
        return value
