terraform {
  backend "s3" {
    bucket               = "tf-state-manager"
    workspace_key_prefix = "face-blurer"
    region               = "eu-central-1"
    dynamodb_table       = "tf-state-manager"
    key                  = "terraform.tfstate"
  }
}