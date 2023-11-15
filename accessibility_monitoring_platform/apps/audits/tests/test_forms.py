"""
Test forms of audits app
"""

from ..forms import StatementCheckCreateUpdateForm
from ..models import STATEMENT_CHECK_TYPE_CHOICES, STATEMENT_CHECK_TYPE_OVERVIEW


def test_statement_overview_not_in_type_choices():
    """Tests statement overview has been removed from type choices"""

    form: StatementCheckCreateUpdateForm = StatementCheckCreateUpdateForm()

    assert len(form.fields["type"].choices) == len(STATEMENT_CHECK_TYPE_CHOICES) - 1
    assert STATEMENT_CHECK_TYPE_OVERVIEW not in [
        value for value, _ in form.fields["type"].choices
    ]
