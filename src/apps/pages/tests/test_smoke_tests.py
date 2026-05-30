from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from factories import CompetitionFactory, TaskFactory, UserFactory


class SmokeTests(TestCase):

    def test_front_page(self):
        assert self.client.get(reverse('pages:home')).status_code == 200

    def test_home_assignment_links_to_matching_competition(self):
        competition = CompetitionFactory(
            title="Assignment 2: Traveling Salesperson (TSP)",
            published=True,
        )

        response = self.client.get(reverse('pages:home'))

        assert response.status_code == 200
        assert bytes(f'href="{competition.get_absolute_url()}"', "utf-8") in response.content

    def test_home_resources_use_box_url_when_configured(self):
        with patch.dict("os.environ", {"COURSE_RESOURCES_BOX_URL": "https://box.nju.edu.cn/f/course-share"}, clear=False):
            response = self.client.get(reverse('pages:home'))

        assert response.status_code == 200
        assert response.content.count(b'href="https://box.nju.edu.cn/f/course-share"') == 4

    def test_student_home_hides_admin_navigation(self):
        student = UserFactory(username="student", password="test")
        self.client.force_login(student)

        response = self.client.get(reverse('pages:home'))

        assert response.status_code == 200
        assert reverse('pages:server_status').encode() not in response.content
        assert b"My Resources" not in response.content
        assert b'selenium="resources"' not in response.content

    def test_staff_home_shows_admin_navigation(self):
        staff = UserFactory(username="teacher", password="test", is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse('pages:home'))

        assert response.status_code == 200
        assert reverse('pages:server_status').encode() in response.content
        assert b"My Resources" in response.content
        assert b'selenium="resources"' in response.content

    def test_student_cannot_access_admin_pages(self):
        student = UserFactory(username="student2", password="test")
        task = TaskFactory()

        self.client.force_login(student)

        admin_urls = [
            reverse('pages:server_status'),
            reverse('pages:monitor_queues'),
            reverse('competitions:management'),
            reverse('competitions:create'),
            reverse('competitions:upload'),
            reverse('datasets:management'),
            reverse('datasets:create'),
            reverse('queues:management'),
            reverse('tasks:task_management'),
            reverse('tasks:detail', args=[task.pk]),
        ]

        for url in admin_urls:
            response = self.client.get(url)
            assert response.status_code == 403

    def test_staff_can_access_admin_pages(self):
        staff = UserFactory(username="teacher2", password="test", is_staff=True)
        task = TaskFactory()

        self.client.force_login(staff)

        admin_urls = [
            reverse('pages:server_status'),
            reverse('pages:monitor_queues'),
            reverse('competitions:management'),
            reverse('competitions:create'),
            reverse('competitions:upload'),
            reverse('datasets:management'),
            reverse('datasets:create'),
            reverse('queues:management'),
            reverse('tasks:task_management'),
            reverse('tasks:detail', args=[task.pk]),
        ]

        for url in admin_urls:
            response = self.client.get(url)
            assert response.status_code == 200
