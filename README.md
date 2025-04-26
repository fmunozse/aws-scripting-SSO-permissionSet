# AWS Identity Center Permission Sets Extractor

This Python script retrieves all Permission Sets from AWS Identity Center (SSO), including their metadata, inline policies, permissions boundaries, managed policies, and tags. The extracted data is saved in a structured output directory (`out/<permissionSet>/*.json`). The script supports filtering Permission Sets by prefix, suffix, or regular expression.

## Prerequisites

- **Python 3.6+**
- **AWS SDK for Python (boto3)**: Install using:
  ```bash
  pip install boto3
  ```
- **AWS Credentials**: Configure AWS credentials with appropriate permissions (see below).
- **AWS SSO Enabled**: Ensure AWS Single Sign-On is enabled in your AWS account.

## Required AWS Permissions

To execute this script, the AWS IAM user or role must have the following permissions for AWS SSO Admin APIs. Attach the following IAM policy to the user or role:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sso-admin:ListInstances",
                "sso-admin:ListPermissionSets",
                "sso-admin:DescribePermissionSet",
                "sso-admin:GetInlinePolicyForPermissionSet",
                "sso-admin:GetPermissionsBoundaryForPermissionSet",
                "sso-admin:ListManagedPoliciesInPermissionSet",
                "sso-admin:ListTagsForResource"
            ],
            "Resource": "*"
        }
    ]
}
```

**Note**: The `Resource` is set to `"*"` as some actions (e.g., `ListInstances`) do not support resource-level restrictions. For more restrictive policies, you can limit the `Resource` to specific SSO instance ARNs where applicable (e.g., `"arn:aws:sso:::instance/ssoins-*"`).

## Usage

Run the script using the following command format:

```bash
python aws_identity_center_permission_sets.py [--filter-type <type>] [--pattern <pattern>]
```

### Arguments

- `--filter-type`: Type of filter to apply. Options: `prefix`, `suffix`, `regex`. Optional.
- `--pattern`: Pattern to match against Permission Set names. Required if `--filter-type` is specified.

### Examples

1. **Retrieve all Permission Sets** (no filter):
   ```bash
   python aws_identity_center_permission_sets.py
   ```

2. **Filter Permission Sets by prefix** (e.g., names starting with "Admin"):
   ```bash
   python aws_identity_center_permission_sets.py --filter-type prefix --pattern Admin
   ```

3. **Filter Permission Sets by suffix** (e.g., names ending with "ReadOnly"):
   ```bash
   python aws_identity_center_permission_sets.py --filter-type suffix --pattern ReadOnly
   ```

4. **Filter Permission Sets by regular expression** (e.g., names containing "Dev"):
   ```bash
   python aws_identity_center_permission_sets.py --filter-type regex --pattern ".*Dev.*"
   ```

## Output

The script creates an `out` directory in the working directory with the following structure for each matching Permission Set:

```
out/
  <PermissionSetName>/
    metadata.json        # Metadata (name, description, ARN, etc.)
    inline-policy.json  # Inline policy, if present
    boundary.json       # Permissions boundary, if present
    managed-policies.json # Attached managed policies, if present
    tags.json           # Tags, if present
```

## Error Handling

- If a Permission Set lacks a specific component (e.g., inline policy, boundary, managed policies, or tags), the corresponding file will not be created.
- Errors (e.g., missing permissions or invalid regex patterns) are printed to the console.
- Ensure both `--filter-type` and `--pattern` are provided together, or the script will display an error.

## Notes

- **Regular Expressions**: The `--pattern` for `regex` filter must be a valid Python regular expression. For example, `.*Dev.*` matches any name containing "Dev". Escape special characters if necessary.
- **AWS Credentials**: Ensure AWS credentials are configured (e.g., via AWS CLI, environment variables, or IAM role).
- **File System Permissions**: The script requires write access to the working directory to create the `out` directory and files.
- **Comprehensive Extraction**: The script extracts:
  - **Metadata**: Name, description, ARN, creation date, session duration, and relay state.
  - **Inline Policy**: Embedded policy document, if defined.
  - **Permissions Boundary**: Boundary policy, if defined.
  - **Managed Policies**: List of attached AWS or customer-managed policies.
  - **Tags**: Key-value pairs for resource organization.

For further assistance, refer to the [AWS SSO Admin API documentation](https://docs.aws.amazon.com/singlesignon/latest/APIReference/Welcome.html).
