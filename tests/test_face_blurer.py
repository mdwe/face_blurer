import pytest
import os
import logging
import boto3
from pathlib import Path
from PIL import Image
from botocore.exceptions import ClientError
from botocore.stub import Stubber
from face_blurer import SourceImage, upload_image_to_s3, lambda_handler, detect_faces

logger = logging.getLogger(__name__)


@pytest.fixture
def trigger_event() -> dict:
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": "face-blurer-origin",
                        "arn": "arn:aws:s3:::face-blurer-origin"
                    },
                    "object": {
                        "key": "faces.jpg",
                        "size": 242112,
                        "eTag": "a780cc2d5eff2d4bbe94ae057caaf980",
                        "sequencer": "0060AA760E4DAC552D"
                    }
                }
            }
        ]
    }


@pytest.fixture
def source_image(trigger_event) -> SourceImage:
    return SourceImage(
        bucket_arn=trigger_event["Records"][0]['s3']['bucket']['arn'],
        bucket_name=trigger_event["Records"][0]['s3']['bucket']['name'],
        file_key=trigger_event["Records"][0]['s3']['object']['key'],
    )


@pytest.fixture
def rekognition_response() -> dict:
    return {
        "FaceDetails": [
            {
                "BoundingBox": {
                    "Width": 0.07742541283369064,
                    "Height": 0.12193935364484787,
                    "Left": 0.06883594393730164,
                    "Top": 0.30593985319137573
                }
            },
            {
                "BoundingBox": {
                    "Width": 0.06968332827091217,
                    "Height": 0.12774230539798737,
                    "Left": 0.710835337638855,
                    "Top": 0.29824575781822205
                }
            },
            {
                "BoundingBox": {
                    "Width": 0.06777414679527283,
                    "Height": 0.11184204369783401,
                    "Left": 0.3366282880306244,
                    "Top": 0.2819172143936157
                }
            }
        ]
    }


@pytest.fixture
def origin_bucket_with_sample_image(origin_bucket):
    _, add_file_to_bucket, bucket_name = origin_bucket

    image_path = Path(os.path.dirname(os.path.abspath(__file__))) / "sample_images" / "faces.jpg"
    for file_path, content in [
        ("faces.jpg", open(image_path, 'rb'))
    ]:
        add_file_to_bucket(file_path=file_path, content=content)


def test_event_processing_with_faces(
    env_variables,
    trigger_event,
    source_image,
    mocker
):
    faces = mocker.patch("face_blurer.detect_faces", return_value=["test"])
    mocker.patch("face_blurer.Blurer.blur", return_value=True)
    response = lambda_handler(trigger_event, {})

    assert response.get("statusCode") == 201
    faces.assert_called_once()


def test_event_processing_without_faces(
    env_variables,
    trigger_event,
    source_image,
    mocker
):
    faces = mocker.patch("face_blurer.detect_faces", return_value=[])
    response = lambda_handler(trigger_event, {})

    assert response.get("statusCode") == 200
    assert response.get("body") == "Faces have been not detected"
    faces.assert_called_once()


def test_event_processing_with_exception(
    trigger_event,
    mocker
):
    mocker.patch("face_blurer.detect_faces", side_effect=Exception('mocked error'))
    response = lambda_handler(trigger_event, {})

    assert response.get("statusCode") == 500
    assert response.get("body") == "Internal server error"


def test_save_file_in_destination_bucket(
    destination_bucket,
    tmp_dir
):
    source_image_path = "test/faces.jpg"
    image_path = Path(os.path.dirname(os.path.abspath(__file__))) / "sample_images" / "faces.jpg"
    image = Image.open(image_path)
    s3_response = upload_image_to_s3(image, "face-blurer-destination", source_image_path)
    assert s3_response.get("ResponseMetadata").get("HTTPStatusCode") == 200

    client = boto3.client('s3')
    results = client.list_objects(Bucket="face-blurer-destination", Prefix=source_image_path)
    assert "Contents" in results


def test_save_file_in_destination_non_existing_bucket():
    source_image_path = "test/faces.jpg"
    image_path = Path(os.path.dirname(os.path.abspath(__file__))) / "sample_images" / "faces.jpg"
    image = Image.open(image_path)
    with pytest.raises(ClientError):
        upload_image_to_s3(image, "face-blurer-destination", source_image_path)


def test_detect_faces(
    source_image,
    origin_bucket_with_sample_image,
    rekognition_response,
    mocker
):
    client = boto3.client('rekognition')
    stubber = Stubber(client)
    detect_faces_response = rekognition_response
    expected_params = {
        'Attributes': ['ALL'],
        'Image': {'S3Object': {'Bucket': 'face-blurer-origin', 'Name': 'faces.jpg'}}
    }
    stubber.add_response('detect_faces', detect_faces_response, expected_params)

    with stubber:
        faces = detect_faces(source_image, client)

    assert faces == rekognition_response["FaceDetails"]
