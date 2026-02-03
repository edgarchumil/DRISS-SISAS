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
            "roles",
        ]

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
        UserProfile.objects.update_or_create(user=user, defaults={"municipality": municipality})
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
            UserProfile.objects.update_or_create(
                user=instance, defaults={"municipality": municipality}
            )
        if groups is not None:
            instance.groups.set(groups)
        return instance
