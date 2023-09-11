"""
Utilities for aws prototype
"""
import json
from typing import Dict, List, Tuple

AWS_RESOURCE_TAGS = {
    "Product": "Accessibility-Monitoring-Platform",
    "System": "Platform | Viewer",
    "Environment": "Prototype",
    "Owner": "a11y-monitoring-cicd-mgmt@digital.cabinet-office.gov.uk",
    "Source": "https://github.com/alphagov/accessibility-monitoring-platform",
}


def get_aws_resource_tags(system: str = "Platform") -> str:
    """Return comma-delimited string of tag names and value pairs"""
    resource_tags: Dict[str, str] = AWS_RESOURCE_TAGS.copy()
    resource_tags["System"] = system
    tag_name_value_pairs: List[Tuple[str, str]] = [
        f"{key}={value}" for key, value in resource_tags.items()
    ]
    return f"--resource-tags {','.join(tag_name_value_pairs)}"


def write_prototype_platform_metadata(git_branch_name: str, prototype_name: str):
    """
    Write prototype metadata to json file for use in platform settings
    """
    aws_prototype_filename: str = "aws_prototype.json"
    with open(aws_prototype_filename, "w") as aws_prototype_file:
        aws_prototype_file.write(
            json.dumps(
                {
                    "prototype_name": git_branch_name,
                    "amp_protocol": "https://",
                    "viewer_domain": f"viewer-svc.env{prototype_name}.app{prototype_name}"
                    ".proto.accessibility-monitoring.service.gov.uk",
                },
                indent=4,
            )
        )
