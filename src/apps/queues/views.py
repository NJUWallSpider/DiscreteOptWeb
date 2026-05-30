from django.views.generic import TemplateView
from utils.permissions import StaffUserRequiredMixin


class QueueManagementView(StaffUserRequiredMixin, TemplateView):
    template_name = 'queues/management.html'
