# EJ-Terraform

Terraform configuration for the "Experience Jamf (EJ)" environment.

Provider versions used in this release:

- deploymenttheory/jamfpro v0.1.5
- danjamf/jsctfprovider v0.0.11

This project utlizes the unoffical Terraform providers for [Jamf Pro](https://registry.terraform.io/providers/deploymenttheory/jamfpro/latest) and [Jamf Security Cloud](https://registry.terraform.io/providers/danjamf/jsctfprovider/latest)

## Prerequisites

While this project is private, you'll need to authenticate against GitHub to clone this repository. We advise you generate a Personal Access Token (PAT) in GitHub settings. Once done, you can follow the commands below.

## Project Initialization

Open a Terminal window and enter the following commands. Replace the following placeholders:

- [BRANCH-NAME]: The name of the branch to clone (main, danwork, vincent-work, etc)
- [PAT]: Your Personal Access Token (you may receive additional SSO login prompts upon first use)
- [FIRST.LAST]: Your local user directory

```
git clone -b [BRANCH-NAME] https://[PAT]@github.com/jamf/TJE-Terraform.git /Users/[FIRST.LAST]/TJE-terraform/
cd /Users/[FIRST.LAST]/TJE-terraform
terraform init
```

## Parallelism and API delay

This project running a big amount of API commands to create a full Jamf Pro configuration, some testings indicate that lowering Terraform parallelism from 10 to 1 reduces the chances of API call errors. Run this command before applying your configuration

```
export TF_CLI_ARGS_apply="-parallelism=1"
```

We also recommend setting the `mandatory_request_delay_milliseconds`provider key to 100.

## Variables definition

This Terraform project requires Jamf API credentials and other context-specific variables that you'll need to define locally in a terraform.tfvars file.

```
cd /Users/[FIRST.LAST]/TJE-terraform
nano terraform.tfvars
```

Copy and paste the following data then customize it with your own credentials

```
jamfpro_instance_url = "https://[MY_SERVER].jamfcloud.com"
jamfpro_auth_method = "" #oauth2 or basic
jamfpro_client_id = ""
jamfpro_client_secret = ""
jamfpro_username = ""
jamfpro_password = ""
radar_user = ""
radar_pass = ""

## Knobs
include_jamfpro_prerequisites = true
include_ej_base = true
include_ej_saas_tenancy = true
include_ej_incident_response = true
include_ej_mobile_cis_benchmark = true
include_ej_mac_cis_benchmark = true
include_ej_secure_remote_access = true
include_jamfpro_demo_config = true
include_jsc_demo_config = true
include_sandbox = false
```

Save and exit.

## Usage

Ensure that you are in the correct project folder when performing Terraform commands (e.g.: /Users/[FIRST.LAST]/TJE-terraform/)

Enter the following command to apply full Terraform config:

```
terraform apply
```

Enter this command to only apply specific modules:

```
terraform apply -target "module.[MODULE_NAME]"
```

N.b. by default all modules will be applied. You can unselect individual modules by modifing the module knobs in your tfvars file e.g.

```
include_ej_mac_cis_benchmark = false
```

## Modules

Each module can be applied individually to test EJ vignettes:

- module.ej_base
- module.ej_incident_response
- module.ej_mac_cis_benchmark
- module.ej_mobile_cis_benchmark
- module.ej_secure_remote_access

Other modules are also available for more general purpose:

- module.jamfpro_demo_config
- module.jsc_demo_config

Want to experiment with your own config? Use this module:

- module.sandbox
