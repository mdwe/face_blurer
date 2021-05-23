import json
import boto3
from PIL import Image, ImageFilter, ExifTags
from io import BytesIO
from math import floor
from os import path, environ
from dataclasses import dataclass

from pprint import pprint


@dataclass
class SourceImage:
    bucket_arn: str
    bucket_name: str
    file_key: str


def lambda_handler(event, context):
    destination_bucket = environ.get("destination_bucket")
    record = event['Records'][0]
    source_image = SourceImage(
        bucket_arn=record['s3']['bucket']['arn'],
        bucket_name=record['s3']['bucket']['name'],
        file_key=record['s3']['object']['key'],
    )

    faces_boundaries = detect_faces(source_image)

    # Blur faces form 
    blurer = Blurrer(source_image)
    blurer.blur_boundaries(faces_boundaries)
    blurer.save(destination_bucket=destination_bucket)

    return {
        'statusCode': 200,
        'body': f"Blurred image {source_image}"
    }

def detect_faces(source_image: SourceImage) -> dict:
    # use AWS rekognition for source image file
    client = boto3.client('rekognition')
    response = client.detect_faces(
        Image={'S3Object': {'Bucket': source_image.bucket_name, 'Name': source_image.file_key}},
        Attributes=['ALL']
    )

    print(f"Detected {len(response['FaceDetails'])} faces for photo {source_image.file_key}")
    return response['FaceDetails']


class Blurrer:
    def __init__(self, source_image: SourceImage):
        self.bucket = source_image.bucket_name
        self.photo = source_image.file_key

        self._loadImage()

    def blur_boundaries(self, boundaries) -> None:
        for boundary in boundaries:
            self._blur_boundary(boundary)

    def _loadImage(self):
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
            self.format = 'JPEG'
        if extension in ['.png']:
            self.format = 'PNG'

    def _blur_boundary(self, face: dict) -> None:
        boundaries = face["BoundingBox"]
        print(self.img.size)
        boundaries_box = (
            floor(self.img.size[0] * boundaries["Left"]),
            floor(self.img.size[1] * boundaries["Top"]),
            floor(self.img.size[0] * boundaries["Left"] + self.img.size[0] * boundaries["Width"]),
            floor(self.img.size[1] * boundaries["Top"] + self.img.size[1] * boundaries["Height"])
        )

        print(f"Crop for {boundaries_box}")
        crop_img = self.img.crop(boundaries_box)

        width, height = crop_img.size
        PIXELATED_RATIO = 60
        MIN_PIXEL_SIZE = 10
        new_width = max(MIN_PIXEL_SIZE, int(width/PIXELATED_RATIO))
        new_hight = max(MIN_PIXEL_SIZE, int(height/PIXELATED_RATIO))
        pixelated_image_small = crop_img.resize((new_width, new_hight), resample=Image.BILINEAR)
        pixelated_image = pixelated_image_small.resize((width, height), resample=Image.NEAREST)
        self.img.paste(pixelated_image, boundaries_box)

    def save(self, destination_bucket):
        buffer = BytesIO()
        self.img.save(buffer, self.format)
        buffer.seek(0)
        s3 = boto3.resource('s3')
        # Uploading the image
        obj = s3.Object(
            bucket_name=destination_bucket,
            key=self.photo
        )
        obj.put(Body=buffer)
        print(f"File saved at {destination_bucket}/{self.photo}")
