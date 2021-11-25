"""
Test forms of audits app
"""

from ..forms import AxeCheckResultUpdateForm


def test_wcag_definition_is_required_on_check_result_update():
    """Tests wcag definition field is required"""
    form: AxeCheckResultUpdateForm = AxeCheckResultUpdateForm(data={})

    assert not form.is_valid()
    assert form.errors == {"wcag_definition": ["Please choose a violation."]}
