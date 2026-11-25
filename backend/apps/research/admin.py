from django.contrib import admin

from .models import ResearchProject


@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "description", "owner__username")
