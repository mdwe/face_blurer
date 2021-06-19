resource "aws_s3_bucket" "origin" {
  bucket        = "${var.project}-origin-${terraform.workspace}"
  acl           = "private"
  force_destroy = true
  tags          = local.tags
}


resource "aws_s3_bucket" "destination" {
  bucket        = "${var.project}-destination-${terraform.workspace}"
  acl           = "private"
  force_destroy = true
  tags          = local.tags
}
