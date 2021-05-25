"""
Views for cases
"""
from django.views.generic.list import ListView

from .models import Case


class CaseListView(ListView):
    model = Case
