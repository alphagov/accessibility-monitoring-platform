"""
Test aws prototype utilities
"""
import pytest

from ..utils import get_aws_resource_tags


@pytest.mark.parametrize("system", ["Platform", "Viewer"])
def test_get_aws_resource_tags(system):
    assert (
        get_aws_resource_tags(system=system)
        == "--resource-tags Product=Accessibility-Monitoring-Platform,"
        f"System={system},Environment=Prototype,"
        "Owner=a11y-monitoring-cicd-mgmt@digital.cabinet-office.gov.uk,"
        "Source=https://github.com/alphagov/accessibility-monitoring-platform"
    )
