resource "aws_s3_bucket" "origin" {
  bucket        = "${var.project}-origin-${terraform.workspace}"
  acl           = "private"
  force_destroy = true
  tags          = local.tags
}

resource "aws_s3_bucket_policy" "origin" {
  bucket = aws_s3_bucket.origin.id
  
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion"
            ],
            "Principal": "*",
            "Resource": [
                "arn:aws:s3:::face-blurer-origin-midwo/*"
            ]
        }
    ]
}
EOF
}

resource "aws_s3_bucket" "destination" {
  bucket        = "${var.project}-destination-${terraform.workspace}"
  acl           = "private"
  force_destroy = true
  tags          = local.tags
}
