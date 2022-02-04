""" integration tests - dockerbroker -
Manges building, starting and closing the docker images in the docker-compose files"""

from __future__ import annotations
import os
from typing import List, TypedDict


class DockerImagesPathsType(TypedDict):
    """Dictionary type for docker images paths

    Args:
        TypedDict ([type]): type for docker images paths
    """

    tag: str
    path: str


class DockerBroker:
    """
    View tests for users

    Methods
    -------
    launch():
        Builds docker images and cleanly launches the docker compose file

    down():
        Cleanly closes docker compose
    """

    def __init__(
        self, docker_images_paths: List[DockerImagesPathsType], docker_compose_path: str
    ):
        if docker_images_paths is False or docker_compose_path is False:
            raise ValueError(
                "docker_images_paths and docker_compose_path must have values"
            )

        self.docker_images_paths = docker_images_paths
        self.docker_compose_path = docker_compose_path

    def launch(self) -> DockerBroker:
        """Builds docker images and cleanly launches the docker compose file

        Returns:
            DockerBroker: Returns self
        """
        for docker_image in self.docker_images_paths:
            os.system(
                f"docker build -t {docker_image['tag']} -f - . < {docker_image['path']}"
            )
        os.system(f"docker compose -f {self.docker_compose_path} down --volumes")
        os.system(f"docker compose -f {self.docker_compose_path} up -d")
        return self

    def down(self) -> DockerBroker:
        """Cleanly closes docker compose

        Returns:
            DockerBroker: Returns self
        """
        os.system(f"docker compose -f {self.docker_compose_path} down")
        os.system(f"docker compose -f {self.docker_compose_path} down --volumes")
        return self
