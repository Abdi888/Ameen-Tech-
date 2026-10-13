from __future__ import annotations

from typing import Any

from rest_framework import serializers


class StrictSerializer(serializers.Serializer[Any]):
    def to_internal_value(self, data: object) -> dict[str, object]:
        if not isinstance(data, dict):
            raise serializers.ValidationError("Request body must be a JSON object.")
        unknown = sorted(set(data) - set(self.fields))
        if unknown:
            raise serializers.ValidationError({unknown[0]: "This field is not allowed."})
        validated = super().to_internal_value(data)
        if not isinstance(validated, dict):
            raise serializers.ValidationError("Request body must be a JSON object.")
        return validated


class LoginSerializer(StrictSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128, trim_whitespace=False)


class ChangePasswordSerializer(StrictSerializer):
    current_password = serializers.CharField(max_length=128, trim_whitespace=False)
    password = serializers.CharField(max_length=128, trim_whitespace=False)


class PasswordResetSerializer(StrictSerializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(StrictSerializer):
    token = serializers.CharField(max_length=200, trim_whitespace=False)
    password = serializers.CharField(max_length=128, trim_whitespace=False)


def parse(serializer: StrictSerializer) -> dict[str, object]:
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if not isinstance(data, dict):
        return {}
    return data
