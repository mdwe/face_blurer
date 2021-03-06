resource "aws_s3_bucket" "origin" {
  bucket        = "${var.project}-origin-${terraform.workspace}"
  acl           = "private"
  force_destroy = true
  tags          = local.tags

  lifecycle_rule {
    id      = "delete_input_files"
    enabled = true
    prefix  = "*.[jpeg,jpg,png]"
    expiration {
      days = 1
    }
  }
}


resource "aws_s3_bucket" "destination" {
  bucket        = "${var.project}-destination-${terraform.workspace}"
  acl           = "private"
  force_destroy = true
  tags          = local.tags
}
