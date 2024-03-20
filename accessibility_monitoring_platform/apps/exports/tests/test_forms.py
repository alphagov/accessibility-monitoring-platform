"""
Test forms of cases app
"""

from datetime import date
from typing import List, Tuple

import pytest
from django.contrib.auth.models import User

from ..forms import ExportCreateForm
from ..models import Export


@pytest.mark.django_db
def test_clean_case_close_form():
    """Tests export checked for duplicate cutoff date"""

    form: ExportCreateForm = ExportCreateForm(
        data={
            "cutoff_date_0": 20,
            "cutoff_date_1": 1,
            "cutoff_date_2": 2024,
        },
    )

    assert form.is_valid()

    user: User = User.objects.create()
    Export.objects.create(cutoff_date=date(2024, 1, 20), exporter=user)

    form: ExportCreateForm = ExportCreateForm(
        data={
            "cutoff_date_0": 20,
            "cutoff_date_1": 1,
            "cutoff_date_2": 2024,
        },
    )

    assert not form.is_valid()
    assert form.errors == {"cutoff_date": ["Export for this date already exists"]}
