from rest_framework import serializers

from .models import ResearchProject

MAX_TAGS = 20
MAX_TAG_LENGTH = 40


class ResearchProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchProject
        fields = ("id", "title", "description", "research_question", "status", "tags", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        owner = self.context["request"].user
        qs = ResearchProject.objects.filter(owner=owner, title__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("You already have a project with this title.")
        return value

    def validate_tags(self, value):
        if not isinstance(value, list) or not all(isinstance(tag, str) for tag in value):
            raise serializers.ValidationError("Must be a list of strings.")
        cleaned = []
        for tag in value:
            tag = tag.strip().lower()
            if not tag:
                continue
            if len(tag) > MAX_TAG_LENGTH:
                raise serializers.ValidationError(f"Each tag must be at most {MAX_TAG_LENGTH} characters.")
            if tag not in cleaned:
                cleaned.append(tag)
        if len(cleaned) > MAX_TAGS:
            raise serializers.ValidationError(f"At most {MAX_TAGS} tags are allowed.")
        return cleaned
