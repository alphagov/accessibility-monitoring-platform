"""
Test forms of audits app
"""
from ..forms import AuditPageCreateForm


def test_url_is_required_in_page_create_form():
    """Tests AuditPageCreateForm's url field is required"""
    form: AuditPageCreateForm = AuditPageCreateForm(data={})

    assert not form.is_valid()
    assert form.errors == {"url": ["URL is required"]}
