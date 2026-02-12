# views.py
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Invoice


@login_required
def download_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    try:
        file = invoice.file.open("rb")
    except Exception:
        raise Http404("File not found in storage")

    return FileResponse(
        file,
        as_attachment=False,  # forces download
        filename=f"invoice-{invoice.pk}.pdf",
        content_type="application/pdf",
    )
