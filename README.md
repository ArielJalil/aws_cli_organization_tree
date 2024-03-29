# AWS Organization queries using cli

Display your AWS Organization tree or display the list of AWS accounts in your AWS Organization from
 CLI.

## Requirements

1. You will need to install and configure your AWS cli with a profile at your AWS Root Organization account.
    * [AWS cli documentation](https://aws.amazon.com/cli/)

2. This code has been tested using [Python 3.12.1](https://pythoninsider.blogspot.com/2023/12/python-3121-is-now-available.html)

### Python modules not included in the Standatd library

* boto3
* botocore
* click

**Note:** If you are new to Python you can use [PIP](https://pip.pypa.io/en/stable/cli/pip_install/)
 to install the modules mentioned above.

### Consider to install pre-commit

If you are planning to enhance this code it is highly recommended to install [pre-commit](https://pre-commit.com/index.html)
 to speed up development and keep some standard coding style.

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

## Usage

```shell
List AWS accounts in the company Organization or display an Organization tree.

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


i.e.

> python3 org_tree.py

> python3 org_tree.py --account_only --profile YOUR_AWS_CLI_PROFILE
```

## Author and Lincense

This script has been written by [Ariel Jall](https://github.com/ArielJalil) and it is released under
 [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
