"""
Utilities for aws prototype
"""
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
