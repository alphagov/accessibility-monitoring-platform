from this import d
from django.shortcuts import render
from django.views.generic import TemplateView
from typing import Dict, List, Any
from django.http import Http404
from django.shortcuts import render
from django.http import HttpResponse

# # Create your views here.
class HomepageView(TemplateView):
    template_name: str = "homepage/homepage.html"

    # def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
    #     print(">>> load correctly")
    #     return super().get_context_data(**kwargs)

# def detail(request):
#     return render(request, 'homepage/homepage.html')

# def detail(request):
#     return render(request, 'homepage/homepageasdsadasd.html')
