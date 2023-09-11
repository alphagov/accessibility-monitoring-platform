"""
Test aws prototype utilities
"""
import pytest
from unittest.mock import patch, mock_open

from ..utils import get_aws_resource_tags, write_prototype_platform_metadata

GIT_BRANCH_NAME: str = "0001-branch-name"
PROTOTYPE_NAME: str = "0001r"


@pytest.mark.parametrize("system", ["Platform", "Viewer"])
def test_get_aws_resource_tags(system):
    """Test expected tags are added to AWS objects"""
    assert (
        get_aws_resource_tags(system=system)
        == "--resource-tags Product=Accessibility-Monitoring-Platform,"
        f"System={system},Environment=Prototype,"
        "Owner=a11y-monitoring-cicd-mgmt@digital.cabinet-office.gov.uk,"
        "Source=https://github.com/alphagov/accessibility-monitoring-platform"
    )


def test_write_prototype_platform_metadata():
    """Test expected metadata for platform settings is written for prototypes"""
    with patch("aws_prototype.utils.open", mock_open()) as mock_file:
        write_prototype_platform_metadata(
            git_branch_name=GIT_BRANCH_NAME, prototype_name=PROTOTYPE_NAME
        )

        mock_file.assert_called_once_with("aws_prototype.json", "w")
        mock_file().write.assert_called_once_with(
            "{\n    "
            f'"prototype_name": "{GIT_BRANCH_NAME}",'
            '\n    "amp_protocol": "https://",\n    '
            f'"viewer_domain": "viewer-svc.env{PROTOTYPE_NAME}.app{PROTOTYPE_NAME}'
            '.proto.accessibility-monitoring.service.gov.uk"\n}'
        )
