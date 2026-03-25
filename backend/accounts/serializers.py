from django.contrib.auth.models import Group, User
from rest_framework import serializers

from accounts.models import UserProfile


class MunicipalityField(serializers.CharField):
    def get_attribute(self, instance):
        try:
            return instance.profile.municipality
        except UserProfile.DoesNotExist:
            return ""


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    municipality = MunicipalityField(required=False, allow_blank=True)
    must_change_password = serializers.SerializerMethodField(read_only=True)
    roles = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Group.objects.all(),
        many=True,
        source="groups",
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "password",
            "municipality",
            "must_change_password",
            "roles",
        ]

    def get_must_change_password(self, instance):
        try:
            return bool(instance.profile.must_change_password)
        except UserProfile.DoesNotExist:
            return False

    def _apply_password_state(self, user, password):
        is_temporary = bool(password) and password[0].isdigit()
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "municipality": getattr(user.profile, "municipality", "") if hasattr(user, "profile") else "",
                "must_change_password": is_temporary,
                "temporary_password": password if is_temporary else "",
            },
        )

    def validate(self, attrs):
        if self.instance is None:
            password = attrs.get("password")
            if not password:
                raise serializers.ValidationError(
                    {"password": "La contrasena es obligatoria para crear el usuario."}
                )
        return attrs

    def create(self, validated_data):
        groups = validated_data.pop("groups", [])
        password = validated_data.pop("password", None)
        municipality = validated_data.pop("municipality", "")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        is_temporary = bool(password) and password[0].isdigit()
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "municipality": municipality,
                "must_change_password": is_temporary,
                "temporary_password": password if is_temporary else "",
            },
        )
        if groups:
            user.groups.set(groups)
        return user

    def update(self, instance, validated_data):
        groups = validated_data.pop("groups", None)
        password = validated_data.pop("password", None)
        municipality = validated_data.pop("municipality", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if municipality is not None:
            profile_defaults = {"municipality": municipality}
            if password:
                is_temporary = password[0].isdigit()
                profile_defaults["must_change_password"] = is_temporary
                profile_defaults["temporary_password"] = password if is_temporary else ""
            UserProfile.objects.update_or_create(user=instance, defaults=profile_defaults)
        elif password:
            is_temporary = password[0].isdigit()
            UserProfile.objects.update_or_create(
                user=instance,
                defaults={
                    "municipality": getattr(instance.profile, "municipality", "")
                    if hasattr(instance, "profile")
                    else "",
                    "must_change_password": is_temporary,
                    "temporary_password": password if is_temporary else "",
                },
            )
        if groups is not None:
            instance.groups.set(groups)
        return instance
