"""
Context processors
"""

import re

PAGE_TITLES = {
    "/cases/": "Cases and reports",
    "/cases/[id]/view/": "View case",
    "/cases/[id]/edit-contact-details/": "Edit case | Contact details",
    "/cases/[id]/archive-case/": "Delete case"
}


def page_title(request):
    """Lookup the page title and place it in context for template rendering"""
    url_without_id = re.sub(r'\d+', "[id]", request.path)
    return {
        "page_title": PAGE_TITLES.get(url_without_id, "Accessibility Monitoring Platform"),
    }