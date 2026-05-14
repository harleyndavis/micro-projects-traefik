from rest_framework import serializers
from .models import Link


class LinkSerializer(serializers.ModelSerializer):
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = Link
        fields = [
            "id",
            "original_url",
            "short_code",
            "short_url",
            "clicks",
            "qr_scans",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "short_code",
            "short_url",
            "clicks",
            "qr_scans",
            "created_at",
        ]

    def get_short_url(self, obj):
        request = self.context.get("request")
        if request:
            return f"{request.scheme}://{request.get_host()}/s/{obj.short_code}"
        return f"/s/{obj.short_code}"


class LinkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ["original_url"]
        extra_kwargs = {
            "original_url": {"validators": []},
        }
