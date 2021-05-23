module "blurer_lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "face-blurer"
  description   = "FaceBlurer Lambda"
  handler       = "face_blurer.lambda_handler"
  runtime       = "python3.8"
  source_path   = "../src"
  timeout       = 90
  memory_size   = 512

  tags          = local.tags
  layers        = ["arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-python38-Pillow:10"]

  environment_variables = {
    "destination_bucket" = aws_s3_bucket.destination.bucket
  }
}


# ************************* Lambda IAM ************************* #
resource "aws_iam_policy" "blurer" {
  name = "${var.project}-${terraform.workspace}-blurer"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "rekognition:*",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": "${aws_s3_bucket.destination.arn}/*"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "blurer" {
  role       = module.blurer_lambda.lambda_role_name
  policy_arn = aws_iam_policy.blurer.arn
}
# ************************************************************** #


# ************ Lambda trigger from Origin S3 bucket ************ #
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.blurer_lambda.lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.origin.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.origin.id

  lambda_function {
    lambda_function_arn = module.blurer_lambda.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}
# ************************************************************** #
