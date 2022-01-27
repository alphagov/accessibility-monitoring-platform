from django.shortcuts import render
from django.views.generic import TemplateView
from .utils import get_overdue_cases


class OverdueView(TemplateView):
    """
    View of list of overdue tasks for user
    """
    template_name = "overdue/overdue_list.html"

    def get_context_data(self, *args, **kwargs):
        context = super(OverdueView, self).get_context_data(*args, **kwargs)
        in_correspondence = get_overdue_cases(user_request=self.request.user)  # type: ignore
        if in_correspondence:
            context["number_of_overdue"] = len(in_correspondence)
        else:
            context["number_of_overdue"] = 0
        context["overdue_cases"] = in_correspondence
        return context
