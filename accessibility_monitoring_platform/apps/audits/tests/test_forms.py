"""
Test forms of audits app
"""
from ..forms import AuditPageForm


def test_url_is_required_in_audit_page_form():
    """Tests AuditPageForm's url field is required"""
    form: AuditPageForm = AuditPageForm(data={})

    assert not form.is_valid()
    assert form.errors == {"url": ["URL is required"]}
