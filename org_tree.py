# -*- coding: utf-8 -*-
"""List AWS accounts in the company Organization or display an Organization
tree.

Usage: org_tree.py [OPTIONS]

  Display AWS Organization tree and/or AWS Accounts - Only Active accounts
  will be displayed.

Options:

  --ou_only / --no-ou_only        Display Organization Units (OUs) only
                                  [default: no-ou_only]
  --account_only / --no-account_only
                                  Display AWS Accounts list  [default: no-
                                  account_only]
  -p, --profile TEXT              Select AWS cli profile name of your root
                                  Organization account from ~/.aws/config file
                                  [default: default]
  -r, --region TEXT               Select AWS Region  [default: ap-southeast-2]
  -e, --environment [ALL|PROD|NON-PROD]
                                  Display AWS Accounts by environment type in
                                  your own name convention  [default: ALL]
  --help                          Show this message and exit.
"""

import os
import sys
import click        # pylint: disable=import-error
import botocore     # pylint: disable=import-error
import boto3        # pylint: disable=import-error


def display_exception(msg):
    """Show excepion messages and abort."""
    print(f"ERROR | Boto3 session failed with error message below:\n {msg}")
    sys.exit()


class AwsSession:
    """Manage boto3 session."""

    def __init__(self, profile: str, region: str):
        """Create Dynamo DB resource."""
        self.profile = profile
        self.region = region

    def cli(self):
        """Start a session to be used from CLI."""
        cli_cache = os.path.join(os.path.expanduser('~'), '.aws/cli/cache')
        try:
            session = boto3.Session(
                profile_name=self.profile,
                region_name=self.region
            )
        except botocore.exceptions.ProfileNotFound as e:
            display_exception(e)

        except Exception as e:  # pylint: disable=broad-exception-caught
            display_exception(e)

        session._session.get_component(  # pylint: disable=protected-access
            'credential_provider'
        ).get_provider(
            'assume-role'
        ).cache = botocore.credentials.JSONFileCache(
            cli_cache
        )

        return session

    def lambdas(self):
        """Start a session to be used in a Lambda funcion."""
        try:
            session = boto3.Session(region_name=self.region)
        except Exception as e:  # pylint: disable=broad-exception-caught
            display_exception(e)

        return session


ELBOW = "└── "
TEE = "├── "
PIPE = "│   "
SPACE = "    "


def get_env(account_alias: str) -> str:
    """Get environment from AWS Account Alias."""
    if '-non-prod' in account_alias:
        environment = 'NON-PROD'
    else:
        environment = 'PROD'

    return environment


def fix_account_alias(ac: dict) -> dict:
    """Manual fixes for account created with wrong aliases."""
    if ac['Email'] == 'XXXXXXXX@example.com':
        ac['Name'] = 'Name to display'
    elif ac['Email'] == 'YYYYYYYY@example.com':
        ac['Name'] = 'Name to display'

    return ac


def get_sorted_items(list_of_dict: list, key: str) -> list:
    """Sort a list of dictionaries by a key."""
    return sorted(
        list_of_dict,
        key=lambda k: k[key]
    )


def paginate(client: object, method: str, **kwargs) -> list:
    """Paginate boto3 clients."""
    paginator = client.get_paginator(method)
    for page in paginator.paginate(**kwargs).result_key_iters():
        for result in page:
            yield result


def fix_sort_accounts(accounts: list) -> list:
    """Fix odd aws account name and sort aphabetically."""
    accounts_fixed_name = []
    for ac in accounts:
        accounts_fixed_name.append(fix_account_alias(ac))

    active_accounts = [
        ac for ac in accounts_fixed_name if ac['Status'] == 'ACTIVE'
    ]
    return get_sorted_items(active_accounts, 'Name')


def display_org_accounts(environment: str) -> None:
    """Display active Accounts in the Organization in alphabetical order."""
    ac_counter = 0
    aws_accounts = list(paginate(ORG, 'list_accounts'))
    sorted_accounts = fix_sort_accounts(aws_accounts)

    for ac in sorted_accounts:
        if environment == 'ALL':
            ac_counter += 1
            print(f"{ac_counter:02d},{ac['Name']},{ac['Id']},{ac['Email']}")
        else:
            account_env = get_env(ac['Name'])
            if environment == account_env:
                ac_counter += 1
                print(f"{ac_counter:02d},{ac['Name']},{ac['Id']},{ac['Email']}")  # noqa: E501


def get_ou_accounts(parent_id: str) -> list:
    """List AWS accounts per Organization Unit."""
    ou_accounts = []
    accounts_list = list(
        paginate(ORG, 'list_accounts_for_parent', ParentId=parent_id)
    )
    if accounts_list:
        sorted_accounts = fix_sort_accounts(accounts_list)
        for a in sorted_accounts:
            ou_accounts.append(
                {
                    'Type': 'A',
                    'Name': a['Name'],
                    'Id': a['Id']
                }
            )

    return ou_accounts


def get_ous(parent_id: str) -> list:
    """List Organization OUs per Parent OU."""
    ous = []
    for ou in paginate(ORG, 'list_organizational_units_for_parent', ParentId=parent_id):  # pylint: disable=line-too-long # noqa: E501
        ous.append(
            {
                'Type': 'OU',
                'Name': ou['Name'],
                'Id': ou['Id']
            }
        )

    return ous


def display_tree(parent_ou, prefix, ou_only):
    """Display directories and files as a directory tree recursively."""
    # Get the list to display
    inner_ou_list = get_ous(parent_ou)
    if not ou_only:
        inner_ou_list += get_ou_accounts(parent_ou)

    while inner_ou_list:
        i = inner_ou_list.pop()
        if inner_ou_list:
            fork = TEE
        else:
            fork = ELBOW

        if i['Type'] == 'OU':
            print(f"{prefix}{PIPE}")

        print(f"{prefix}{fork}< {i['Id']} > | {i['Name']}")

        if i['Type'] == 'OU':
            if inner_ou_list:
                new_prefix = prefix + PIPE
            else:
                new_prefix = prefix + SPACE

            display_tree(i['Id'], new_prefix, ou_only)


@click.command()
@click.option(
    '--ou_only/--no-ou_only',
    default=False,
    show_default=True,
    help='Display Organization Units (OUs) only'
)
@click.option(
    '--account_only/--no-account_only',
    default=False,
    show_default=True,
    help='Display AWS Accounts list'
)
@click.option(
    '-p',
    '--profile',
    default='default',
    show_default=True,
    nargs=1,
    help='Select AWS cli profile name of your root Organization account from ~/.aws/config file'  # pylint: disable=line-too-long # noqa: E501
)
@click.option(
    '-r',
    '--region',
    default='ap-southeast-2',
    show_default=True,
    nargs=1,
    help='Select AWS Region'
)
@click.option(
    '-e',
    '--environment',
    default='ALL',
    show_default=True,
    nargs=1,
    type=click.Choice(['ALL', 'PROD', 'NON-PROD'], case_sensitive=False),
    help='Display AWS Accounts by environment type in your own name convention'
)
def org_tree(account_only: bool, ou_only: bool, environment: str, profile: str, region: str) -> None:  # pylint: disable=line-too-long # noqa: E501
    """Display AWS Organization tree and/or AWS Accounts Only Active accounts
    will be displayed."""
    session_obj = AwsSession(
        profile,        # AWS cli profile name of the root account in the Org.
        region
    )
    session = session_obj.cli()
    global ORG  # pylint: disable=global-variable-undefined
    ORG = session.client('organizations')

    if account_only:
        display_org_accounts(environment)
    else:
        org_details = ORG.describe_organization()
        roots = ORG.list_roots()
        org_root_id = roots['Roots'][0]['Id']
        # Print Organization Unit root level
        print(f"\nOrganization ID: {org_details['Organization']['Id']}\n")
        print(f"/ Root OU [ Id: {org_root_id} ]\n{PIPE}")
        # Display organization tree recursively
        display_tree(org_root_id, '', ou_only)


if __name__ == '__main__':
    org_tree()  # pylint: disable=no-value-for-parameter
