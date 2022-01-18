"""
Test forms of audits app
"""
from ..forms import AuditExtraPageUpdateForm


def test_url_is_required_in_page_form():
    """Tests AuditExtraPageUpdateForm's url field is required"""
    form: AuditExtraPageUpdateForm = AuditExtraPageUpdateForm(data={})

    assert not form.is_valid()
    assert form.errors == {"url": ["URL is required"]}
