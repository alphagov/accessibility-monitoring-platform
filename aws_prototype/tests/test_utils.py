"""
Test aws prototype utilities
"""
from ..utils import get_aws_resource_tags


def test_get_aws_resource_tags():
    assert (
        get_aws_resource_tags(system="Viewer")
        == "--resource-tags Product=Accessibility Monitoring Platform,"
        "System=Viewer,Environment=Prototype,"
        "Owner=a11y-monitoring-cicd-mgmt@digital.cabinet-office.gov.uk,"
        "Source=https://github.com/alphagov/accessibility-monitoring-platform"
    )
