"""
Python script to orchestrate the integration tests
"""
import time
from app.check_docker_django_has_started import check_docker_django_has_started
from app.download_s3_object import download_s3_object
from app.download_webdriver import download_webdriver
from app.run_pytest_suite import run_pytest_suite
from app.parse_json import parse_integration_tests_json
from app.DockerBroker import DockerBroker
from app.parse_json import IntegrationTestsSettingsType
import argparse

parser = argparse.ArgumentParser(description="Settings for integration tests")

parser.add_argument(
    "-s" "--settings-json", dest="settings_json", help="Path for json settings"
)

if __name__ == "__main__":
    args = parser.parse_args()
    start = time.time()
    settings: IntegrationTestsSettingsType = parse_integration_tests_json(
        settings_path=args.settings_json
    )
    db: DockerBroker = DockerBroker(
        docker_images_paths=settings["docker_images_paths"],
        docker_compose_path=settings["docker_compose_path"],
    )

    for S3object in settings["s3_objects"]:
        download_s3_object(
            s3_bucket=settings["s3_bucket"],
            s3_path=S3object["s3_path"],
            local_path=S3object["local_path"],
        )

    if settings["ignore_docker"]:
        print("Skipping docker")
    else:
        db.launch()
        check_docker_django_has_started(
            max_attempts=settings["connect_attempts"],
            endpoint=settings["testing_endpoint"],
        )

    download_webdriver(chrome_version=settings["chrome_version"])

    run_pytest_suite(
        path_for_xml_results=settings["path_for_xml_results"],
        test_dir=settings["test_dir"],
    )

    if not settings["ignore_docker"]:
        db.down()

    end: float = time.time()
    print("Testing took", end - start, "seconds")
