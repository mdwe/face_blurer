import logging
import os
import pytest
import boto3
import cv2
import numpy
from pathlib import Path
from integration_tests.environment_config_manager.env_config_parser import (
    EnvConfigParser,
)
from integration_tests.environment_config_manager.env_resource_operations import (
    upload_file,
    check_if_files_exist_in_bucket,
    delete_file,
)


@pytest.fixture
def upload_images_list() -> list:
    return [
        "46950216-large-group-of-people-community-teamwork-concept.jpg",
        "children-playing-at-home.jpg",
        "draw-facial-features_lee-hammond_artists-network_portrait-drawing-demo-3.jpg",
        "scotch-faces-portraits-2.jpg",
        "women-face-portrait-blonde-wallpaper-preview.jpg",
    ]


def test_face_blur(
    environment_config: EnvConfigParser,
    logger: logging.Logger,
    buckets_config: dict,
    upload_images_list: list,
    tmp_dir: str,
):
    source_image_path = (
        Path(os.path.dirname(os.path.abspath(__file__))) / "images" / "source"
    )
    blured_image_path = (
        Path(os.path.dirname(os.path.abspath(__file__))) / "images" / "blured"
    )

    # Remove required files from destination bucket if any exists
    for file_name in upload_images_list:
        delete_file(buckets_config["destination_bucket"], file_name)

    assert (
        check_if_files_exist_in_bucket(
            buckets_config["destination_bucket"], "", upload_images_list, 0, 1
        )
        is False
    )

    for file_name in upload_images_list:
        upload_file(
            str(source_image_path / file_name),
            buckets_config["origin_bucket"],
            file_name,
        )
    logger.info("All files have been uploaded to S3!")

    assert check_if_files_exist_in_bucket(
        buckets_config["origin_bucket"], "", upload_images_list,
    )
    # Check destination bucket for blured files
    assert check_if_files_exist_in_bucket(
        buckets_config["destination_bucket"], "", upload_images_list,
    )

    s3 = boto3.client("s3")
    for file_name in upload_images_list:
        local_file_path = str(Path(tmp_dir) / file_name)

        # Download files for comparison
        s3.download_file(
            buckets_config["destination_bucket"], file_name, local_file_path
        )
        logger.info(f"File has been downloaded: {local_file_path}")

        # Compare blured images with expected output
        generated_image = cv2.imread(local_file_path)
        blured_image = cv2.imread(str(blured_image_path / file_name))

        assert generated_image.shape == blured_image.shape

        diff = cv2.absdiff(generated_image, blured_image)
        diff = diff.astype("uint8")
        percentage = (numpy.count_nonzero(diff) * 100) / diff.size
        assert percentage < 5
