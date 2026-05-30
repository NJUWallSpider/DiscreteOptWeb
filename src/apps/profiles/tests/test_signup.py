from django.test import TestCase, override_settings
from django.urls import reverse

from profiles.models import User


class SignUpTests(TestCase):
    @override_settings(ENABLE_SIGN_UP=False)
    def test_signup_redirects_to_login_when_disabled(self):
        response = self.client.get(reverse("accounts:signup"))

        self.assertRedirects(response, reverse("accounts:login"))

    @override_settings(ENABLE_SIGN_UP=True)
    def test_signup_creates_inactive_user_and_waits_for_admin_approval(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "student1",
                "email": "student1@example.com",
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            },
        )

        self.assertRedirects(response, reverse("pages:home"))
        created_user = User.objects.get(username="student1")
        self.assertFalse(created_user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(ENABLE_SIGN_UP=True)
    def test_signup_allows_blank_email_without_server_error(self):
        first_response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "student3",
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            },
        )
        second_response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "student4",
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            },
        )

        self.assertRedirects(first_response, reverse("pages:home"))
        self.assertRedirects(second_response, reverse("pages:home"))
        self.assertIsNone(User.objects.get(username="student3").email)
        self.assertIsNone(User.objects.get(username="student4").email)

    @override_settings(ENABLE_SIGN_UP=True)
    def test_inactive_user_sees_pending_approval_message_on_login(self):
        User.objects.create_user(
            username="student2",
            email="student2@example.com",
            password="StrongPassword123",
            is_active=False,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "student2",
                "password": "StrongPassword123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "awaiting administrator approval")
