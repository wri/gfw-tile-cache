{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Principal": {
        "AWS": "${aws_resource_arn}"
      },
      "Resource": "${bucket_arn}"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "${aws_resource_arn}"
      },
      "Action": "s3:GetObject",
      "Resource": "${bucket_arn}/*"
    }
  ]
}