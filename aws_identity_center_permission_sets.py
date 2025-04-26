import boto3
import json
import os
import re
import argparse
from botocore.exceptions import ClientError

def filter_permission_set(name, filter_type, pattern):
    """Filtra el nombre del Permission Set según el tipo de filtro y el patrón."""
    if filter_type == "prefix":
        return name.startswith(pattern)
    elif filter_type == "suffix":
        return name.endswith(pattern)
    elif filter_type == "regex":
        return bool(re.match(pattern, name))
    return True  # Si no se especifica filtro, incluye todos

def get_permission_sets_and_policies(filter_type=None, pattern=None):
    # Initialize AWS SSO Admin client
    sso_admin = boto3.client('sso-admin')
    
    # Create output directory
    output_dir = "out"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Get Identity Store ID and Instance ARN
        response = sso_admin.list_instances()
        instance_arn = response['Instances'][0]['InstanceArn']
        
        # List all Permission Sets
        permission_sets = []
        paginator = sso_admin.get_paginator('list_permission_sets')
        for page in paginator.paginate(InstanceArn=instance_arn):
            permission_sets.extend(page['PermissionSets'])
        
        for ps_arn in permission_sets:
            # Get Permission Set details
            ps_details = sso_admin.describe_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=ps_arn
            )['PermissionSet']
            
            permission_set_name = ps_details['Name']
            
            # Aplicar filtro
            if not filter_permission_set(permission_set_name, filter_type, pattern):
                continue
                
            ps_dir = os.path.join(output_dir, permission_set_name)
            os.makedirs(ps_dir, exist_ok=True)
            
            # Save Metadata
            metadata = {
                'Name': ps_details.get('Name'),
                'Description': ps_details.get('Description'),
                'PermissionSetArn': ps_details.get('PermissionSetArn'),
                'CreatedDate': ps_details.get('CreatedDate').isoformat(),
                'SessionDuration': ps_details.get('SessionDuration'),
                'RelayState': ps_details.get('RelayState')
            }
            with open(os.path.join(ps_dir, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Get Inline Policy
            try:
                inline_policy = sso_admin.get_inline_policy_for_permission_set(
                    InstanceArn=instance_arn,
                    PermissionSetArn=ps_arn
                )['InlinePolicy']
                
                if inline_policy:
                    with open(os.path.join(ps_dir, 'inline-policy.json'), 'w') as f:
                        json.dump(json.loads(inline_policy), f, indent=2)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    print(f"Error getting inline policy for {permission_set_name}: {e}")
            
            # Get Permissions Boundary (if exists)
            try:
                boundary = sso_admin.get_permissions_boundary_for_permission_set(
                    InstanceArn=instance_arn,
                    PermissionSetArn=ps_arn
                )['PermissionsBoundary']
                
                with open(os.path.join(ps_dir, 'boundary.json'), 'w') as f:
                    json.dump(boundary, f, indent=2)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    print(f"Error getting boundary for {permission_set_name}: {e}")
            
            # Get Managed Policies
            try:
                managed_policies = sso_admin.list_managed_policies_in_permission_set(
                    InstanceArn=instance_arn,
                    PermissionSetArn=ps_arn
                )['AttachedManagedPolicies']
                
                with open(os.path.join(ps_dir, 'managed-policies.json'), 'w') as f:
                    json.dump(managed_policies, f, indent=2)
            except ClientError as e:
                print(f"Error getting managed policies for {permission_set_name}: {e}")
            
            # Get Tags
            try:
                tags = sso_admin.list_tags_for_resource(
                    InstanceArn=instance_arn,
                    ResourceArn=ps_arn
                )['Tags']
                
                with open(os.path.join(ps_dir, 'tags.json'), 'w') as f:
                    json.dump(tags, f, indent=2)
            except ClientError as e:
                print(f"Error getting tags for {permission_set_name}: {e}")
                    
        print(f"Permission sets and policies have been saved to {output_dir}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve AWS SSO Permission Sets with filters")
    parser.add_argument('--filter-type', choices=['prefix', 'suffix', 'regex'],
                        help="Type of filter to apply (prefix, suffix, or regex)")
    parser.add_argument('--pattern', help="Pattern to match (prefix, suffix, or regex pattern)")
    
    args = parser.parse_args()
    
    if args.filter_type and not args.pattern:
        print("Error: --pattern is required when --filter-type is specified")
    elif args.pattern and not args.filter_type:
        print("Error: --filter-type is required when --pattern is specified")
    else:
        get_permission_sets_and_policies(args.filter_type, args.pattern)
