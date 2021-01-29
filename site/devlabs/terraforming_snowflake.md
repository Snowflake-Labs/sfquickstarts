summary: This is an introduction to using Terraform to manage Snowflake
id: terraforming_snowflake
categories: getting-started 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/devlabs/issues
tags: Getting Started, Data Science, Data Engineering, Data Applications, Terraform
authors: Brad Culberson

# Terraforming Snowflake

## Overview 
Duration: 5

[Terraform](https://www.terraform.io/) is an open-source infrastructure as code tool created by HashiCorp. A [provider](https://registry.terraform.io/providers/chanzuckerberg/snowflake/latest/docs) is available for Snowflake (written by Chan Zuckerberg Initiative) as well as the cloud providers we host on: [Azure](https://registry.terraform.io/providers/hashicorp/azurerm/latest), [AWS](https://registry.terraform.io/providers/hashicorp/aws/latest/docs), and [GCP](https://registry.terraform.io/providers/hashicorp/google/latest).

Being declarative, you define the resources and configurations you want and Terraform will calculate the dependencies, look at previous state and make all necessary change to converge to the new desired state.

This is a very easy way to deploy new projects, make infrastructure changes in production, and REALLY convenient for managing dependencies between providers.

Examples:
 - Set up storage in your cloud provider and adding it to Snowflake as an external stage
 - Add storage and connect it to Snowpipe
 - Create a service user and push the key (or rotate) into the secrets manager of your choice.

 Many customers prefer to have their infrastructure as code to abide by their compliance controls, maintain consistency, support similar engineering workflows for infrastructure as other updates.

In this tutorial we will show you how to install and use Terraform to create and manage your Snowflake environment. We will create a Database, Schema, Warehouse, Roles, and a Service User. This will show you how you could use Terraform to manage your Snowflake configurations in an automated and source controlled way.

We will not cover a specific cloud provider or how to integrate Terraform into specific ci/cd tool in this introduction to Snowflake due the variety used by different customers. Those may be covered (separately) in future labs content.

### Prerequisites
- Familiarity with Git, Snowflake, and Snowflake objects
- AccountAdmin role access to a Snowflake account

### What You’ll Learn 
- basic usage of Terraform
- how to create users, roles, databases, schemas, warehouses in Terraform
- how to manage objects from code/source control

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- Git command line client
- Text editor of your choice
- [Terraform](https://www.terraform.io/downloads.html) Installed

### What You’ll Build 
- A repository containing a Terraform project that manages Snowflake account objects through code

## Create a New Repository
Duration: 5

 - [Create](https://github.com/new) a new repository to hold your Terraform project. For this example we will use the name tf-snow. Here are the commands to use if you use the git command line client:

```Shell
$ mkdir tf-snow && cd tf-snow 
$ echo "# tf-snow" >> README.md
$ git init
$ git add README.md
$ git commit -m "first commit"
$ git branch -M main
$ GHUSER=`git config user.name`
$ git remote add origin git@github.com:${GHUSER}/tf-snow.git
$ git push -u origin main
```

You now have an empty repo. We will use this repo in subsequent steps to Terraform your Snowflake account.

If you have problems with the commands above, check that your ssh key is setup properly with Github and your git config is correct for your account.


## Create a Service User for Terraform
Duration: 5

We will now create a separate user from your own which will use key pair authenticaion. This is primarily done in this lab due to limitations in the provider to cache credentials and lack of support of 2fa. It will also be how most ci/cd pipelines will run Terraform leveraging service users.

### Create an RSA key for Authentication

This will create the private and public key we can use to authenticate the service user we'll use
for Terraform.

```Shell
$ cd ~/.ssh
$ openssl genrsa -out snowflake_tf_snow_key 4096
$ openssl rsa -in snowflake_tf_snow_key -pubout -out snowflake_tf_snow_key.pub
```

### Create the User in Snowflake

Log into the Snowflake console and create the user by running this command as ACCOUNTADMIN role.

Copy the contents of text from `~/.ssh/snowflake_tf_snow_key.pub` file after the PUBLIC KEY header and before the PUBLIC KEY footer over the `RSA_PUBLIC_KEY_HERE` text below.

Execute both sql statements below to create the user and grant it access to the SYSADMIN and SECURITYADMIN role needed for account management.

```SQL
CREATE USER "tf-snow" RSA_PUBLIC_KEY='RSA_PUBLIC_KEY_HERE' DEFAULT_ROLE=PUBLIC MUST_CHANGE_PASSWORD=FALSE;

GRANT ROLE SYSADMIN TO USER "tf-snow";
GRANT ROLE SECURITYADMIN TO USER "tf-snow";
```

While we are granting this user SYSADMIN and SECURITYADMIN in this case for simplicity, it is a best practice to limit all user accounts to least priviledges. In your production environments, this key should also be well secured leveraging technologies like Hashicorp Vault, Azure Key Vault, or AWS Secrets Manager.

## Setup Terraform Authentication
Duration: 1

In order for Terraform to authenticate as the user we'll need to pass the provider information needed via environment variables and input variables for Terraform. 

Find your `YOUR_SNOWFLAKE_ACCOUNT_HERE` and `YOUR_SNOWFLAKE_REGION_HERE` values needed from the Snowflake console by running:

```SQL
select current_account(), current_region();
```

### Add Account Information to Environment

Run these commands in your shell, make sure to replace the YOUR_SNOWFLAKE_ACCOUNT_HERE and YOUR_SNOWFLAKE_REGION_HERE text with the values found from previous query results.

```Shell
$ export SNOWFLAKE_USER="tf-user"
$ export SNOWFLAKE_PRIVATE_KEY_PATH="~/.ssh/snowflake_tf_snow_key"
$ export SNOWFLAKE_ACCOUNT="YOUR_SNOWFLAKE_ACCOUNT_HERE"
$ export SNOWFLAKE_REGION="YOUR_SNOWFLAKE_REGION_HERE"
```

If you plan on working on this/more project(s) in multiple shells, it may be convenient to put this in an `snow.env` file you can source or put it in your `.bashrc` or `.zshrc`. For this lab we'll expect you to run future terraform commands in a shell with those set.

## Declaring Resources
Duration: 3

Add a file to your project in the base directroy named main.tf. In main.tf we will setup the provider as well as define the configuration for the database and the warehouse we want Terraform to create.

Copy the contents of this block to your main.tf

```JSON
terraform {
  required_providers {
    snowflake = {
      source  = "chanzuckerberg/snowflake"
      version = "0.22.0"
    }
  }
}

provider "snowflake" {
  role     = "SYSADMIN"
}

resource "snowflake_database" "db" {
  name = "TF_DEMO"
}

resource "snowflake_warehouse" "warehouse" {
  name           = "TF_DEMO"
  warehouse_size = "xsmall"

  auto_suspend = 60
}
```

This is all the code needed to create these resources.

## Preparing the Project to Run
Duration: 3

In order to setup the project to run Terraform, you'll need to initialize the project.

From a shell in your project folder run:

```Shell 
$ terraform init
```

This will download the dependencies needed to run Terraform onto your computer.

In this demo we will be using local state for Terraform. The state files are requried to calculate all changes and are extremely important to merge changes correctly in the future. If Terraform is ran by multiple users and/or on different computers and/or through CI/CD the state files, state **SHOULD REALLY** be put in [Remote Storage](https://www.terraform.io/docs/language/state/remote.html). While using local state, you'll see the current state stored in `*.tfstate` and old versions named `*.tfstate.*`.

The `.terraform` folder is where all the dependencies are downloaded, it is safe to add that as well as the state files to the `.gitignore` to minimize changes.

Create a file in your project root named .gitignore with this for the contents:

```plaintext
*.terraform*
*.tfstate
*.tfstate.*
```

## Commit those changes to source control
Duration: 2

We will now check these in for future change tracking.

```Shell
$ git checkout -b dbwh
$ git add main.tf
$ git add .gitignore
$ git commit -m "Add Database and Warehouse"
$ git push origin HEAD
```

You can login to Github, create a Pull Request.

In many production systems, the commit to Github triggers the CI/CD job which does a plan for review. The engineers can then review that for changes and merge the Pull Request if the changes are desired. After merge, a CI/CD job kicks off to apply the changes now made in main branch.

In order to manage the different environments (dev/test/prod) resources can be named to isolate from each other or you can use separate Snowflake accounts to reduce complexity and blast radius. If the environment is passed as an [input variable](https://www.terraform.io/docs/language/values/variables.html) to the project, you can run the same Terraform project unchanged for each environment.

Your workflow will be dependent on your environment and account topology, requirements, workflows, and compliance needs.

For this lab, you can simulate the CI/CD job proposed and do a plan to see what Terraform wants to change. During plan, Terraform will compare it's known and stored state with what is in the desired resources and display all changes needed to conform the resources. 

From a shell in your project folder (with your Account Information in environment) run:

```Shell
$ terraform plan
```

## Running Terraform
Duration: 3

Now that you have reviewed the plan, we will also simulate the next step of the CI/CD job by applying those changes to your account.

From a shell in your project folder (with your Account Information in environment) run:

```Shell
$ terraform apply
```

Terraform will recreate the plan, and when verified by you apply all changes needed. In this case you should see that Terraform will be creating 2 new resources and have no other changes.

Login to your Snowflake Account and verify that the database and the warehouse has been created.

## Changing and Adding Resources
Duration: 5

All databases need a Schema to store tables so we'll add that as well as a service user so our application/client can connect to the database and schema. You will see this syntax is very similar to the database and warehouse you already created, you have already learned everything you need to know to create and update resources in Snowflake. We'll also add priviledges so the service role/user can use the database and schema.

You'll see most of this is what you expected, the only complicated part is really the private key creation as Terraform tls private key generator doesn't export the public key in a format the Terraform provider can consume so some string manipulations are needed.

Change the warehouse size in the main.tf file from `xsmall` to `small`.

Also, add the following resources to your main.tf file:

```JSON
provider "snowflake" {
  alias    = "security_admin"
  role     = "SECURITYADMIN"
}

resource "snowflake_role" "role" {
  provider = snowflake.security_admin
  name     = "TF_DEMO_SVC_ROLE"
}

resource "snowflake_database_grant" "grant" {
  database_name = snowflake_database.db.name

  privilege = "USAGE"
  roles     = [snowflake_role.role.name]

  with_grant_option = false
}

resource "snowflake_schema" "schema" {
  database = snowflake_database.db.name
  name     = "TF_DEMO"

  is_managed = false
}

resource "snowflake_schema_grant" "grant" {
  database_name = snowflake_database.db.name
  schema_name   = snowflake_schema.schema.name

  privilege = "USAGE"
  roles     = [snowflake_role.role.name]

  with_grant_option = false
}

resource "snowflake_warehouse_grant" "grant" {
  warehouse_name = snowflake_warehouse.warehouse.name
  privilege      = "USAGE"

  roles = [snowflake_role.role.name]

  with_grant_option = false
}

resource "tls_private_key" "svc_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "snowflake_user" "user" {
  provider = snowflake.security_admin
  name     = "tf_demo_user"

  default_warehouse = snowflake_warehouse.warehouse.name
  default_role      = snowflake_role.role.name
  default_namespace = "${snowflake_database.db.name}.${snowflake_schema.schema.name}"
  rsa_public_key    = substr(tls_private_key.svc_key.public_key_pem, 27, 398)
}

resource "snowflake_role_grants" "grants" {
  role_name = snowflake_role.role.name
  users     = [snowflake_user.user.name]
}
```

In order to get the public and private key information for the application we can use Terraform [output variables](https://www.terraform.io/docs/language/values/outputs.html).

Add the following resources to a new file named outputs.tf

```JSON
output "snowflake_svc_public_key" {
  value = tls_private_key.svc_key.public_key_pem
}

output "snowflake_svc_private_key" {
  value = tls_private_key.svc_key.private_key_pem
}
```

## Commit Changes to Source Control
Duration: 3

We will now check these in for future change tracking.

```Shell
$ git checkout -b svcuser
$ git add main.tf
$ git add outputs.tf
$ git commit -m "Add Service User, Schema, Grants"
$ git push origin HEAD
```

You can login to Github to create the Pull Request and Merge the changes.

## Apply and Verify the Changes
Duration: 2

In order to simulate the CI/CD pipeline we can then apply those changes again to conform the desired state with the stored state.

From a shell in your project folder (with your Account Information in environment) run:

```Shell
$ terraform apply
```

Accept the changes if they look appropriate and login to the console to see all the changes
complete.

With all changes stored in source control and applied by CI/CD you get a history of all your environment changes. Authorization to manage the environments directly can be constrained to fewer users and compliance controls can be put into place. But also this makes it easy to bring up new environments that are identical to others in a timely manner without managing sql scripts.

## Cleanup
Duration: 1

You're almost complete with the demo, but we have one thing left to do. Lets cleanup your account.

### Destroy all the Terraform Managed Resources

From a shell in your project folder (with your Account Information in environment) run:

```Shell
$ terraform destroy
```

Accept the changes if they look appropriate and login to the console to see all the objects are destroyed.

### Drop the User we added

From your Snowflake console run:

```SQL
DROP USER "tf-snow";
```

## Conclusion
Duration: 3

If you are new to Terraform there is still a lot to learn. We suggest you research [remote state](https://www.terraform.io/docs/language/state/remote.html), [input variables](https://www.terraform.io/docs/language/values/variables.html), and [building modules](https://www.terraform.io/docs/language/modules/develop/index.html). This will empower you to build and manage your Snowflake environment(s) through a simple declarative language.

The Terraform provider for Snowflake is an open-source project, we would love your help making it better. If you need Terraform to manage a resource that has not yet been created in the [provider](https://registry.terraform.io/providers/chanzuckerberg/snowflake/latest), we welcome contributions. We also highly encourage you to submit issues and feedback to the [Github Project](https://github.com/chanzuckerberg/terraform-provider-snowflake) so we can all make the project and experience better.

Next Steps for you are to decide how you will run your Terraform changes. In this demo we ran all of this on your local computer but that is rarely done in production environments. Best practices will have ci/cd pipelines which automate all workflows changing shared environments. This will allow for better gates to change those environments as well as an audit trail in source control to review the history of an environment.

You will want to make the decision of how you isolate your environments and projects whether via namespacing/RBAC or via multiple accounts. Changing this later will be very difficult as most modules and ci/cd infrastructure will need to be heavily modified for the alternative approach.

You may also need to evaluate other tools to complete your infrastructure management. Terraform is a powerful tool for managing many resources in Snowflake but does have limitations managing schema and data changes. More robust tools are available to manage things like data migrations and table schema changes.

If you had any issues with this project you can pull [a working version](https://github.com/Snowflake-Labs/sfguide-terraform-sample) directly from Github.

### What we've covered
- Getting started with Terraform
- Setting up a new project
- Adding a new Database, Warehouse, Schema, User, Role, and Grants
- Destroying all the resources
