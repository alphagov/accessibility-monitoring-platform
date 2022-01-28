from django.shortcuts import render
from django.views.generic import TemplateView


class ReportGeneratorBase(TemplateView):
    """
    View of list of overdue tasks for user
    """
    template_name = "report_generator/base.html"
