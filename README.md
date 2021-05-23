# FaceBlurer

## System requirements:

- terraform
- python 3.8
- awsume

## Installation 

### Build AWS infrastructure

#### Prepare AWS requirements [backend.tf]

Create manualy bucket for backend S3 with name `tf-state-manager` with **enable Bucket Versioning**. Backend also supports state locking and consistency checking via Dynamo DB, which can defined by `dynamodb_table` field - create DynamoDB table with name `tf-state-manager`, the table must have a primary key named LockID with type of string.

#### Build FaceBlurer

Execute all Terraform commands from `infrastructure` directory.

1. Create terraform workspace

```
terraform workspace new $workspace_name
terraform workspace select $workspace_name
```

2. Init Terraform project

```
terraform init
```

3. Apply terraform project to AWS

```
terraform apply -var-file=development/development.tfvars --auto-approve
```

**Destroy environment:**

```
terraform destroy -var-file=development/development.tfvars --auto-approve
```