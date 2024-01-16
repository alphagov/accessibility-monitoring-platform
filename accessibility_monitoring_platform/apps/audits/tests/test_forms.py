"""
Test forms of audits app
"""

from ..forms import StatementCheckCreateUpdateForm
from ..models import StatementCheck


def test_statement_overview_not_in_type_choices():
    """Tests statement overview has been removed from type choices"""

    form: StatementCheckCreateUpdateForm = StatementCheckCreateUpdateForm()

    assert len(form.fields["type"].choices) == len(StatementCheck.Type.choices) - 1
    assert StatementCheck.Type.OVERVIEW not in [
        value for value, _ in form.fields["type"].choices
    ]
