# FaceBlurer

## System requirements:

- terraform
- python 3.8
- awsume

## Installation 

### Build AWS infrastructure

#### Prepare AWS requirements [backend.tf]

Create manually bucket for backend S3 with the name `tf-state-manager` with **enable Bucket Versioning**. The backend also supports state locking and consistency checking via Dynamo DB, which can define by the `dynamodb_table` field - create DynamoDB table with the name `tf-state-manager`, the table must have a primary key named LockID with type of string.

#### Build FaceBlurer environment

Execute all Terraform commands from the `infrastructure` directory.

1. Create Terraform workspace

```
terraform workspace new $workspace_name
terraform workspace select $workspace_name
```

2. Init Terraform project

```
terraform init
```

3. Apply Terraform project to AWS

```
terraform apply -var-file=development/development.tfvars --auto-approve
```

**Destroy environment:**

```
terraform destroy -var-file=development/development.tfvars --auto-approve
```

### Python tests

Install tests requirements:

```
pip install -r requirements-test.txt
```

Run unit tests:

```
pytest tests --html=report.html -vv
```

Run integration tests:

```
pytest -vv -x --environment="{terraform_workspace_name}" --tf_state_bucket_name="{tf_state_bucket_name}" integration_tests --html=report.html
```