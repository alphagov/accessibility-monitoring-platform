"""
Utilities for aws prototype
"""

import json
import os
import random
import string

AWS_RESOURCE_TAGS = {
    "Product": "Accessibility-Monitoring-Platform",
    "System": "Platform | Viewer",
    "Environment": "Prototype",
    "Owner": "a11y-monitoring-cicd-mgmt@digital.cabinet-office.gov.uk",
    "Source": "https://github.com/alphagov/accessibility-monitoring-platform",
}


def get_aws_resource_tags(system: str = "Platform") -> str:
    """Return comma-delimited string of tag names and value pairs"""
    resource_tags: dict[str, str] = AWS_RESOURCE_TAGS.copy()
    resource_tags["System"] = system
    tag_name_value_pairs: list[tuple[str, str]] = [
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


def create_burner_account(app_name: str, env_name: str) -> None:
    print(">>> Creating burner account")
    email: str = (
        f"""{"".join(random.choice(string.ascii_lowercase) for x in range(7))}@email.com"""
    )
    password: str = "".join(random.choice(string.ascii_lowercase) for x in range(27))
    command: str = f"python aws_prototype/create_dummy_account.py {email} {password}"
    copilot_exec_cmd = f"""copilot svc exec -a {app_name} -e {env_name} -n amp-svc --command "{command}" """
    os.system(copilot_exec_cmd)
    print(
        f"The platform can be accessed from https://amp-svc.{env_name}.{app_name}.proto.accessibility-monitoring.service.gov.uk"
    )
    print(
        f"The viewer can be accessed from https://viewer-svc.{env_name}.{app_name}.proto.accessibility-monitoring.service.gov.uk"
    )
    print(f"email: {email}")
    print(f"password: {password}")
