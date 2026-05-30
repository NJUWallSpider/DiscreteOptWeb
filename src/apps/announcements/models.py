from django.db import models
from django.utils.timezone import now


class Announcement(models.Model):
    text = models.TextField(null=True, blank=True)


class NewsPost(models.Model):
    title = models.CharField(max_length=40)
    link = models.URLField(max_length=200, blank=True)
    created_when = models.DateTimeField(default=now)
    text = models.TextField(null=True, blank=True)


class HomeAssignment(models.Model):
    ACTIVE = "active"
    CLOSED = "closed"

    STATUS_TONE_CHOICES = [
        (ACTIVE, "Active"),
        (CLOSED, "Closed"),
    ]

    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    status_label = models.CharField(max_length=40, default="Active")
    status_tone = models.CharField(
        max_length=20,
        choices=STATUS_TONE_CHOICES,
        default=ACTIVE,
    )
    icon = models.CharField(max_length=80, default="keyboard outline")
    url = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class CourseResource(models.Model):
    title = models.CharField(max_length=120)
    url = models.CharField(max_length=500, blank=True)
    icon = models.CharField(max_length=80, default="file outline")
    color = models.CharField(max_length=20, default="#1a364d")
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title
