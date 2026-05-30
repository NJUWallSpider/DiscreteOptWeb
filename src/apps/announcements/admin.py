from django.contrib import admin
from . import models


class NewsPostExpansion(admin.ModelAdmin):
    list_display = ["id", "title", "link", "created_when"]
    list_display_links = ["id", "title"]
    search_fields = ["id", "title", "link"]
    ordering = ["-created_when", "-id"]


class AnnouncementExpansion(admin.ModelAdmin):
    list_display = ["id", "text_limited"]
    list_display_links = ["id", "text_limited"]

    @admin.display(description="text", ordering="text")
    def text_limited(self, obj):
        if not obj.text:
            return "-"
        if len(obj.text) > 500:
            return obj.text[:500] + "(...)"
        else:
            return obj.text[:500]


admin.site.register(models.Announcement, AnnouncementExpansion)
admin.site.register(models.NewsPost, NewsPostExpansion)


class HomeAssignmentAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "status_label", "status_tone", "order", "is_visible"]
    list_display_links = ["id", "title"]
    list_editable = ["status_label", "status_tone", "order", "is_visible"]
    search_fields = ["id", "title", "description", "url"]
    list_filter = ["status_tone", "is_visible"]
    ordering = ["order", "id"]


class CourseResourceAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "url", "order", "is_visible"]
    list_display_links = ["id", "title"]
    list_editable = ["order", "is_visible"]
    search_fields = ["id", "title", "url"]
    list_filter = ["is_visible"]
    ordering = ["order", "id"]


admin.site.register(models.HomeAssignment, HomeAssignmentAdmin)
admin.site.register(models.CourseResource, CourseResourceAdmin)
