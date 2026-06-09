from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from urllib.parse import urlparse


def validate_home_link(value):
    if not value:
        return

    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in ("http", "https", "mailto"):
        raise ValidationError("Use an http(s), mailto, or site-relative URL.")
    if not parsed.scheme and (parsed.netloc or not value.startswith("/")):
        raise ValidationError("Relative URLs must start with '/'.")


def validate_hex_color(value):
    if not value:
        return
    if not value.startswith("#") or len(value) not in (4, 7):
        raise ValidationError("Use a hex color such as #f2711c.")
    try:
        int(value[1:], 16)
    except ValueError as exc:
        raise ValidationError("Use a hex color such as #f2711c.") from exc


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

    def clean(self):
        super().clean()
        validate_home_link(self.url)


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

    def clean(self):
        super().clean()
        validate_home_link(self.url)
        validate_hex_color(self.color)
