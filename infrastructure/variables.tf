variable "region" {}
variable "project" {}
variable "account" {}
variable "role" {}
variable "tags" {}


locals {
  local_tags = {
    Environment = terraform.workspace
    Project = "FaceBlurer"
  }
  tags = merge(var.tags, local.local_tags)
}