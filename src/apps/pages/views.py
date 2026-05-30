import copy
import os

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.urls import reverse
from django.views.generic import TemplateView

from competitions.models import Competition, Submission
from announcements.models import Announcement, NewsPost

from django.conf import settings
from utils.data import pretty_bytes
from utils.permissions import StaffUserRequiredMixin


DEFAULT_HOME_ASSIGNMENTS = [
    {
        "title": "Assignment 3: Graph Coloring Problem",
        "description": "Due: May 15, 2026, 11:59 PM • Max Score: 100 pts",
        "status_label": "Active",
        "status_tone": "active",
        "icon": "keyboard outline",
    },
    {
        "title": "Assignment 2: Traveling Salesperson (TSP)",
        "description": "Due: April 30, 2026, 11:59 PM • Max Score: 100 pts",
        "status_label": "Active",
        "status_tone": "active",
        "icon": "keyboard outline",
    },
    {
        "title": "Assignment 1: Knapsack Problem",
        "description": "Ended: Mar 10, 2026 • Graded",
        "status_label": "Closed",
        "status_tone": "closed",
        "icon": "check circle outline",
    },
]

DEFAULT_HOME_RESOURCES = [
    {
        "title": "Course Syllabus",
        "icon": "file pdf outline",
        "color": "#db2828",
        "url_env": "COURSE_SYLLABUS_URL",
    },
    {
        "title": "Lecture Slides & Notes",
        "icon": "file powerpoint outline",
        "color": "#f2711c",
        "url_env": "COURSE_SLIDES_URL",
    },
    {
        "title": "Starter Code Templates",
        "icon": "github",
        "color": "#1b1c1d",
        "url_env": "COURSE_STARTER_CODE_URL",
    },
    {
        "title": "Discussion Forum",
        "icon": "comments outline",
        "color": "#2185d0",
        "url_env": "COURSE_FORUM_URL",
    },
]


def build_home_assignments():
    assignments = copy.deepcopy(DEFAULT_HOME_ASSIGNMENTS)

    for assignment in assignments:
        competition = Competition.objects.filter(
            published=True,
            title__iexact=assignment["title"],
        ).first()
        assignment["url"] = competition.get_absolute_url() if competition else reverse("competitions:public")

    return assignments


def build_home_resources():
    resources = copy.deepcopy(DEFAULT_HOME_RESOURCES)
    shared_box_url = os.environ.get("COURSE_RESOURCES_BOX_URL", "").strip()

    for resource in resources:
        resource["url"] = os.environ.get(resource["url_env"], "").strip() or shared_box_url

    return resources


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        announcement = Announcement.objects.all().first()
        context['announcement'] = announcement.text if announcement else None

        news_posts = NewsPost.objects.all().order_by('-id')
        context['news_posts'] = news_posts
        context['CONTACT_EMAIL'] = settings.CONTACT_EMAIL
        context['home_assignments'] = build_home_assignments()
        context['course_resources'] = build_home_resources()

        return context


class OrganizeView(TemplateView):
    template_name = 'pages/organize.html'


class SearchView(TemplateView):
    template_name = 'search/form.html'


class ServerStatusView(StaffUserRequiredMixin, TemplateView):
    template_name = 'pages/server_status.html'

    def get_context_data(self, *args, **kwargs):

        show_child_submissions = self.request.GET.get('show_child_submissions', False)
        page = self.request.GET.get('page', 1)
        submissions_per_page = 50

        # Start with an empty queryset
        qs = Submission.objects.none()

        user = self.request.user
        # Only if user is authenticated
        if user.is_authenticated:
            # If user is not super user then filter:
            # - this user's own submissions
            # - submissions running on competitions where the user is owner or collaborator
            # - submissions running on queue where the user is owner or organizer
            # NOTE: exclude all soft-deleted submissions
            if not user.is_superuser:
                qs = Submission.objects.filter(is_soft_deleted=False).filter(
                    Q(owner=user) |
                    Q(phase__competition__created_by=user) |
                    Q(phase__competition__collaborators=user) |
                    Q(queue__owner=user, queue__isnull=False) |
                    Q(queue__organizers=user, queue__isnull=False)
                ).distinct()
            else:
                qs = Submission.objects.filter(is_soft_deleted=False)

        # Filter out child submissions i.e. submission has no parent
        if not show_child_submissions:
            qs = qs.filter(parent__isnull=True)

        qs = qs.order_by('-created_when')
        qs = qs.select_related('phase__competition', 'owner')

        # Paginate the queryset
        paginator = Paginator(qs, submissions_per_page)

        try:
            submissions = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver the first page.
            submissions = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results.
            submissions = paginator.page(paginator.num_pages)

        context = super().get_context_data(*args, **kwargs)
        context['submissions'] = submissions
        context['show_child_submissions'] = show_child_submissions

        for submission in context['submissions']:
            # Get filesize from each submissions's data
            if submission.data:
                submission.file_size = pretty_bytes(submission.data.file_size)
            else:
                submission.file_size = pretty_bytes(0)

            # Get queue from each submission
            queue_name = ""
            # if submission has parent get queue from parent otherwise from the submission iteset
            if submission.parent:
                queue_name = "*" if submission.parent.queue is None else submission.parent.queue.name
            else:
                queue_name = "*" if submission.queue is None else submission.queue.name
            submission.competition_queue = queue_name

            # Add submission owner display name
            submission.owner_display_name = submission.owner.display_name if submission.owner.display_name else submission.owner.username

        context['paginator'] = paginator
        context['is_paginated'] = paginator.num_pages > 1

        return context


class MonitorQueuesView(StaffUserRequiredMixin, TemplateView):
    template_name = 'pages/monitor_queues.html'
