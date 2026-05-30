from django.test import TestCase
from django.urls import reverse

from profiles.models import User


class OrganizationCreateViewTests(TestCase):
    def test_non_staff_user_cannot_access_organization_create(self):
        user = User.objects.create_user(
            username="student_org",
            email="student_org@example.com",
            password="StrongPassword123",
            is_active=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("profiles:organization_create"))

        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_access_organization_create(self):
        user = User.objects.create_user(
            username="staff_org",
            email="staff_org@example.com",
            password="StrongPassword123",
            is_active=True,
            is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("profiles:organization_create"))

        self.assertEqual(response.status_code, 200)
