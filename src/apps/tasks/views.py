from django.views.generic import TemplateView, DetailView

from .models import Task
from utils.permissions import StaffUserRequiredMixin


class TaskManagement(StaffUserRequiredMixin, TemplateView):
    template_name = 'tasks/management.html'


class TaskDetailView(StaffUserRequiredMixin, DetailView):
    queryset = Task.objects.all()
    template_name = 'tasks/task_detail.html'
