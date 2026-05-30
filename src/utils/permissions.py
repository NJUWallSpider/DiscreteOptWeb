from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


def user_can_access_admin_area(user):
    return bool(user.is_authenticated and user.is_staff)


class StaffUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return user_can_access_admin_area(self.request.user)
