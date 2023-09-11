Backup Portal Data
==================

Backup Process
--------------

The following process assumes we are performing a backup for batch 5, as an example.

#. Create the db snapshot (we will then back up the snapshot to s3)::

    aws rds create-db-snapshot \
        --db-instance-identifier portal-batch5 \
        --db-snapshot-identifier ldsa-portal-batch5-backup

#. Create a s3 bucket in the same region as the db instance

#. Create the policy to allow the export task to write to the s3 bucket::

    aws iam create-policy  --policy-name ExportPolicy --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ExportPolicy",
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject*",
                    "s3:ListBucket",
                    "s3:GetObject*",
                    "s3:DeleteObject*",
                    "s3:GetBucketLocation"
                ],
                "Resource": [
                    "arn:aws:s3:::ldsa-portal-batch5-backup",
                    "arn:aws:s3:::ldsa-portal-batch5-backup/*"
                ]
            }
        ]
    }'

#. Create an IAM role. You do this so that Amazon RDS can assume this IAM role on your behalf to access your Amazon S3 buckets::

    aws iam create-role  --role-name rds-s3-export-role  --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "export.rds.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
        ]
    }'

#. Attach the IAM policy that you created to the IAM role that you created::

    aws iam attach-role-policy  \
        --policy-arn your-policy-arn  \
        --role-name rds-s3-export-role

#. Create a key, and give it an alias::

    aws kms create-key
    aws kms create-alias \
        --alias-name alias/ldsa-portal-batch5-backup \
        --target-key-id arn:aws:kms:eu-west-1:036806565123:key/754f1adc-3cc7-4578-b06c-61d41de40a4e

#. Run the export task::

    aws rds start-export-task \
        --export-task-identifier ldsa-portal-batch5-backup \
        --source-arn arn:aws:rds:eu-west-1:036806565123:snapshot:ldsa-portal-batch5-backup \
        --s3-bucket-name ldsa-portal-batch5-backup \
        --iam-role-arn arn:aws:iam::036806565123:role/rds-s3-export-role \
        --kms-key-id arn:aws:kms:eu-west-1:036806565123:key/754f1adc-3cc7-4578-b06c-61d41de40a4e

Existing Backups
----------------

* https://s3.console.aws.amazon.com/s3/buckets/ldsa-portal-batch4-backup?region=eu-west-1
* https://s3.console.aws.amazon.com/s3/buckets/ldsa-portal-batch5-backup?region=eu-west-1

Resources
---------

* https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ExportSnapshot.html
* https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_CreateSnapshot.html
* https://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html#create-symmetric-cmk
* https://docs.aws.amazon.com/cli/latest/reference/kms/create-alias.html
