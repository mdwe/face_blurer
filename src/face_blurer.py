import boto3
import logging
from PIL import Image
from io import BytesIO
from math import floor
from os import path, environ
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class SourceImage:
    bucket_arn: str
    bucket_name: str
    file_key: str


def lambda_handler(event, context):
    try:
        destination_bucket = environ.get("destination_bucket")
        record = event['Records'][0]
        source_image = SourceImage(
            bucket_arn=record['s3']['bucket']['arn'],
            bucket_name=record['s3']['bucket']['name'],
            file_key=record['s3']['object']['key'],
        )

        faces_boundaries = detect_faces(source_image)
        if(len(faces_boundaries) == 0):
            return {
                "statusCode": 200,
                "body": "Faces have been not detected"
            }
        # Blur faces form
        blurer = Blurer(source_image, faces_boundaries, destination_bucket)
        blurer.blur()

        return {
            "statusCode": 201,
            "body": f"Blurred image {source_image}"
        }
    except Exception:
        return {
            "statusCode": 500,
            "body": "Internal server error"
        }


def detect_faces(source_image: SourceImage, client=boto3.client('rekognition')) -> dict:
    # use AWS rekognition for source image file
    response = client.detect_faces(
        Image={'S3Object': {'Bucket': source_image.bucket_name, 'Name': source_image.file_key}},
        Attributes=['ALL']
    )

    logger.info(f"Detected {len(response['FaceDetails'])} faces for photo {source_image.file_key}")
    return response['FaceDetails']


def upload_image_to_s3(image: Image, destination_bucket: str, destination_key: str, image_format: str = "JPEG") -> dict:
    buffer = BytesIO()
    image.save(buffer, image_format)
    buffer.seek(0)
    s3 = boto3.resource('s3')

    try:
        obj = s3.Object(
            bucket_name=destination_bucket,
            key=destination_key
        )
        s3_response = obj.put(Body=buffer)
        logger.info(f"File saved at {destination_bucket}/{destination_key}")
        return s3_response
    except Exception as ex:
        logger.error(f"Exeption on upload file to {destination_bucket}/{destination_key}: {ex}")
        raise ex


class Blurer:
    def __init__(self, source_image: SourceImage, faces_boundaries: list, destination_bucket: str):
        self.bucket = source_image.bucket_name
        self.photo = source_image.file_key
        self.faces_boundaries = faces_boundaries
        self.destination_bucket = destination_bucket

    def blur(self) -> None:
        format = self._load_image()
        self._blur_boundaries()
        upload_image_to_s3(self.img, self.destination_bucket, self.photo, format)

    def _load_image(self) -> str:
        s3 = boto3.resource('s3')

        # Grabs the source file
        obj = s3.Object(
            bucket_name=self.bucket,
            key=self.photo,
        )
        obj_body = obj.get()['Body'].read()
        self.img = Image.open(BytesIO(obj_body))

        extension = path.splitext(self.photo)[1].lower()
        if extension in ['.jpeg', '.jpg']:
            format = 'JPEG'
        elif extension in ['.png']:
            format = 'PNG'
        return format

    def _blur_boundaries(self) -> None:
        for boundary in self.faces_boundaries:
            self._blur_boundary(boundary)

    def _blur_boundary(self, face: dict) -> None:
        boundaries = face["BoundingBox"]
        boundaries_box = (
            floor(self.img.size[0] * boundaries["Left"]),
            floor(self.img.size[1] * boundaries["Top"]),
            floor(self.img.size[0] * boundaries["Left"] + self.img.size[0] * boundaries["Width"]),
            floor(self.img.size[1] * boundaries["Top"] + self.img.size[1] * boundaries["Height"])
        )

        logger.debug(f"Crop for {boundaries_box}")
        crop_img = self.img.crop(boundaries_box)

        width, height = crop_img.size
        PIXELATED_RATIO = 60
        MIN_PIXEL_SIZE = 10
        new_width = max(MIN_PIXEL_SIZE, int(width/PIXELATED_RATIO))
        new_hight = max(MIN_PIXEL_SIZE, int(height/PIXELATED_RATIO))
        pixelated_image_small = crop_img.resize((new_width, new_hight), resample=Image.BILINEAR)
        pixelated_image = pixelated_image_small.resize((width, height), resample=Image.NEAREST)
        self.img.paste(pixelated_image, boundaries_box)
