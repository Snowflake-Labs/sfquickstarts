summary: Learn how to manage Snowflake using Terraform
id: terraforming_snowflake
categories: featured,getting-started,app-development,devops
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Data Applications, Terraform
authors: Brad Culberson, Scott Winkler

# Terraforming Snowflake

## Overview
Duration: 5

[Terraform](https://www.terraform.io/) is an open-source Infrastructure as Code (IaC) tool created by HashiCorp. It is a declarative Infrastructure as Code tool, meaning instead of writing step-by-step imperative instructions like with SQL, JavaScript or Python, you can declare what you want using a YAML like syntax. Terraform is also stateful, meaning it keeps track of your current state, and compares it with your desired state. A reconcilation process between the two states generates an plan that Terraform can execute to create new resources, or update/delete existing resources. This plan is implemented as an acyclic graph, and is what allows Terraform to understand and handle dependencies between resources. Using Terraform is a great way to manage account level Snowflake resources like Warehouses, Databases, Schemas, Tables, and Roles/Grants, among many other use cases.  

A Terraform provider is available for [Snowflake](https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest/docs), that allows Terraform to integrate with Snowflake.

Example Terraform use-cases:
 - Set up storage in your cloud provider and add it to Snowflake as an external stage
 - Add storage and connect it to Snowpipe
 - Create a service user and push the key into the secrets manager of your choice, or rotate keys

Many Snowflake customers use Terraform to comply with security controls, maintain consistency, and support similar engineering workflows for infrastructure at scale.

This tutorial demonstrates how you can use Terraform to manage your Snowflake configurations in an automated and source-controlled way. We show you how to install and use Terraform to create and manage your Snowflake environment, including how to create a database, schema, warehouse, multiple roles, and a service user.  

 This introductory tutorial does _not_ cover specific cloud providers or how to integrate Terraform into specific CI/CD tools. Those topics may be covered in future labs.

### Prerequisites
- Familiarity with Git, Snowflake, and Snowflake objects
- `ACCOUNTADMIN` role access to a Snowflake account

### What You’ll Learn
- Basic Terraform usage
- How to create users, roles, databases, schemas, and warehouses in Terraform
- How to manage objects from code/source control

### What You’ll Need
- A [GitHub](https://github.com/) account
- A git command-line client
- Text editor of your choice
- [Terraform](https://www.terraform.io/downloads.html) installed

### What You’ll Build
- A repository containing a Terraform project that manages Snowflake account objects through code

## Create a New Repository
Duration: 5

[Create](https://github.com/new) a new repository to hold your Terraform project. We use the name `sfguide-terraform-sample` in this lab. 

Run the following commands if you use the git command-line client replacing `YOUR_GITHUB_USERNAME` with your username:

```Shell
$ mkdir sfguide-terraform-sample && cd sfguide-terraform-sample
$ echo "# sfguide-terraform-sample" >> README.md
$ git init
$ git add README.md
$ git commit -m "first commit"
$ git branch -M main
$ git remote add origin git@github.com:YOUR_GITHUB_USERNAME/sfguide-terraform-sample.git
$ git push -u origin main
```

> aside positive
> 
>  **Tip** – If the commands don't work, verify that you can connect to GitHub using your SSH key, and that your git config is correct for your account.

You now have an empty repo that we will use in subsequent steps to Terraform your Snowflake account.

## Create a Service User for Terraform
Duration: 5

We will now create a user account separate from your own that uses key-pair authentication. The reason this is required in this lab is due to the provider's limitations around caching credentials and the lack of support for 2FA. Service accounts and key pair are also how most CI/CD pipelines run Terraform.

### Create an RSA key for Authentication

This creates the private and public keys we use to authenticate the service account we will use
for Terraform.

```Shell
$ cd ~/.ssh
$ openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_tf_snow_key.p8 -nocrypt
$ openssl rsa -in snowflake_tf_snow_key.p8 -pubout -out snowflake_tf_snow_key.pub
```

### Create the User in Snowflake

Log in to the Snowflake console and create the user account by running the following command as the `ACCOUNTADMIN` role.

But first:
1. Copy the text contents of the `~/.ssh/snowflake_tf_snow_key.pub` file, starting _after_ the `PUBLIC KEY` header, and stopping just _before_ the `PUBLIC KEY` footer.
1. Paste over the `RSA_PUBLIC_KEY_HERE` label (shown below).

Execute both of the following SQL statements to create the User and grant it access to the `SYSADMIN` and `SECURITYADMIN` roles needed for account management.

```SQL
CREATE USER "tf-snow" RSA_PUBLIC_KEY='RSA_PUBLIC_KEY_HERE' DEFAULT_ROLE=PUBLIC MUST_CHANGE_PASSWORD=FALSE;

GRANT ROLE SYSADMIN TO USER "tf-snow";
GRANT ROLE SECURITYADMIN TO USER "tf-snow";
```

> aside negative
> 
>  We grant the user `SYSADMIN` and `SECURITYADMIN` privileges to keep the lab simple. An important security best practice, however, is to limit all user accounts to least-privilege access. In a production environment, this key should also be secured with a secrets management solution like Hashicorp Vault, Azure Key Vault, or AWS Secrets Manager.

## Setup Terraform Authentication
Duration: 1

We need to pass provider information via environment variables and input variables so that Terraform can authenticate as the user.

Run the following to find the `YOUR_ACCOUNT_LOCATOR` and your Snowflake Region ID values needed.

```SQL
SELECT current_account() as YOUR_ACCOUNT_LOCATOR, current_region() as YOUR_SNOWFLAKE_REGION_ID;
```

You can find your Region ID (`YOUR_REGION_HERE`) from `YOUR_SNOWFLAKE_REGION_ID` in [this reference table](https://docs.snowflake.com/en/user-guide/admin-account-identifier.html#snowflake-region-ids). 

**Example**: aws_us_west_2 would have a us-west-2 value for `YOUR_REGION_HERE`.

### Add Account Information to Environment

Run these commands in your shell. Be sure to replace the `YOUR_ACCOUNT_LOCATOR` and `YOUR_REGION_HERE` placeholders with the correct values.

**NOTE**: Setting `SNOWFLAKE_REGION` is only required if you are using a [Legacy Account Locator](https://docs.snowflake.com/en/user-guide/admin-account-identifier#format-2-legacy-account-locator-in-a-region).

```Shell
$ export SNOWFLAKE_USER="tf-snow"
$ export SNOWFLAKE_PRIVATE_KEY_PATH="~/.ssh/snowflake_tf_snow_key.p8"
$ export SNOWFLAKE_ACCOUNT="YOUR_ACCOUNT_LOCATOR"
$ export SNOWFLAKE_REGION="YOUR_REGION_HERE"
```

If you plan on working on this or other projects in multiple shells, it may be convenient to put this in a `snow.env` file that you can source or put it in your `.bashrc` or `.zshrc` file. For this lab, we expect you to run future Terraform commands in a shell with those set.

## Declaring Resources
Duration: 3

Add a file to your project in the base directory named `main.tf`. In `main.tf` we set up the provider and define the configuration for the database and the warehouse that we want Terraform to create.

Copy the contents of the following block to your `main.tf`

```
terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.68"
    }
  }
}

provider "snowflake" {
  role = "SYSADMIN"
}

resource "snowflake_database" "db" {
  name = "TF_DEMO"
}

resource "snowflake_warehouse" "warehouse" {
  name           = "TF_DEMO"
  warehouse_size = "large"
  auto_suspend   = 60
}
```

This is all the code needed to create these resources.

## Preparing the Project to Run
Duration: 3

To set up the project to run Terraform, you first need to initialize the project.

Run the following from a shell in your project folder:

```Shell
$ terraform init
```

The dependencies needed to run Terraform are downloaded to your computer.

In this demo, we use a local backend for Terraform, which means that state file are stored locally on the machine running Terraform. Because Terraform state files are required to calculate all changes, its critical that you do not lose this file (`*.tfstate`, and `*.tfstate.*` for older state files), or Terraform will lose track of what resources it is managing. For any kind of multi-tenancy or automation workflows, it is highly recommended to use [Remote Backends](https://www.terraform.io/docs/language/state/remote.html), which is outside the scope of this lab.

The `.terraform` folder is where all provider and modules depenencies are downloaded. There is nothing important in this folder and it is safe to delete. You should add this folder, and the Terraform state files (since you do not want to be checking in sensitive information to VCS) to `.gitignore`.

Create a file named `.gitignore` in your project root, then add the following text to the file and save it:

```plaintext
*.terraform*
*.tfstate
*.tfstate.*
```

## Commit  changes to source control
Duration: 2

Run the following to check in your files for future change tracking:

```Shell
$ git checkout -b dbwh
$ git add main.tf
$ git add .gitignore
$ git commit -m "Add Database and Warehouse"
$ git push origin HEAD
```

Next, you can log in to GitHub and create a Pull Request.

In many production systems, a GitHub commit triggers a CI/CD job, which creates a plan that engineers can review. If the changes are desired, the Pull Request is merged. After the merge, a CI/CD job kicks off and applies the changes made in the main branch.

To manage different environments (dev/test/prod), you can configure the Terraform code with different [input variables](https://www.terraform.io/docs/language/values/variables.html) and either deploy to either the same Snowflake account, or different Snowflake accounts. 

Your specific workflow will depend on your requirements, including your compliance needs, your other workflows, and your environment and account topology.

For this lab, you can simulate the proposed CI/CD job and do a plan to see what Terraform wants to change. During the Terraform plan, Terraform performs a diff calculation to compare the desired state with the previous/current state from the state file to determine the acitons that need to be done.

From a shell in your project folder (with your Account Information in environment), run:

```Shell
$ terraform plan
```

## Running Terraform
Duration: 3

Now that you have reviewed the plan, we simulate the next step of the CI/CD job by applying those changes to your account.

1. From a shell in your project folder (with your Account Information in environment) run:

    ```
    $ terraform apply
    ```
1. Terraform regenerates the execution plan (unless you supply an optional path to the `plan.out` file) and applies the needed changes after confirmation. In this case, Terraform will create two new resources, and have no other changes.

1. Log in to your Snowflake account and verify that Terraform created the database and the warehouse.


## Changing and Adding Resources
Duration: 5


All databases need a schema to store tables, so we'll add that and a service user so that our application/client can connect to the database and schema. The syntax is very similar to the database and warehouse you already created. By now you have learned everything you need to know to create and update resources in Snowflake. We'll also add privileges so the service role/user can use the database and schema.

You'll see that most of this is what you would expect. The only new part is creating the private key. Because the Terraform TLS private key generator doesn't export the public key in a format that the Terraform provider can consume, some string manipulations are needed.

1. Change the warehouse size in the `main.tf` file from `xsmall` to `small`.

1. Add the following resources to your `main.tf` file:

```
provider "snowflake" {
  alias = "security_admin"
  role  = "SECURITYADMIN"
}

resource "snowflake_role" "role" {
  provider = snowflake.security_admin
  name     = "TF_DEMO_SVC_ROLE"
}

resource "snowflake_grant_privileges_to_role" "database_grant" {
  provider   = snowflake.security_admin
  privileges = ["USAGE"]
  role_name  = snowflake_role.role.name
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.db.name
  }
}

resource "snowflake_schema" "schema" {
  database   = snowflake_database.db.name
  name       = "TF_DEMO"
  is_managed = false
}

resource "snowflake_grant_privileges_to_role" "schema_grant" {
  provider   = snowflake.security_admin
  privileges = ["USAGE"]
  role_name  = snowflake_role.role.name
  on_schema {
    schema_name = "\"${snowflake_database.db.name}\".\"${snowflake_schema.schema.name}\""
  }
}

resource "snowflake_grant_privileges_to_role" "warehouse_grant" {
  provider   = snowflake.security_admin
  privileges = ["USAGE"]
  role_name  = snowflake_role.role.name
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.warehouse.name
  }
}

resource "tls_private_key" "svc_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "snowflake_grant_privileges_to_role" "user_grant" {
  provider   = snowflake.security_admin
  privileges = ["MONITOR"]
  role_name  = snowflake_role.role.name
  on_account_object {
    object_type = "USER"
    object_name = "tf-snow"
  }
}

resource "snowflake_role_grants" "grants" {
  provider  = snowflake.security_admin
  role_name = snowflake_role.role.name
  users     = ["tf-snow"]
}
```

1. To get the public and private key information for the application, use Terraform [output values](https://www.terraform.io/docs/language/values/outputs.html).

    Add the following resources to a new file named `outputs.tf`

    ```
    output "snowflake_svc_public_key" {
        value = tls_private_key.svc_key.public_key_pem
    }

    output "snowflake_svc_private_key" {
        value     = tls_private_key.svc_key.private_key_pem
        sensitive = true
    }
    ```

## Commit Changes to Source Control
Duration: 3

Let's check in our files for future change tracking:

```Shell
$ git checkout -b svcuser
$ git add main.tf
$ git add outputs.tf
$ git commit -m "Add Service User, Schema, Grants"
$ git push origin HEAD
```

You can log in to Github to create the Pull Request and merge the changes. Pull Requests allow for process controls for reviews
and the centralized git repo can automatically event CI/CD workflows
as desired.


## Apply and Verify the Changes
Duration: 2

To simulate the CI/CD pipeline, we can apply the changes to conform the desired state with the stored state.

1. From a shell in your project folder (with your Account Information in environment) run:

   ```
   $ terraform apply
   ```

1. Accept the changes if they look appropriate.
1. Log in to the console to see all the changes complete.

Because all changes are stored in source control and applied by CI/CD, you can get a [history](https://github.com/Snowflake-Labs/sfguide-terraform-sample/commits/main/main.tf) of all your environment changes. You can put compliance controls into place and limit authorization to directly manage the environments to fewer users. This also makes it easy to bring up new environments that are identical to others in a timely manner without managing SQL scripts.

## Cleanup
Duration: 1

You're almost done with the demo. We have one thing left to do: clean up your account.

### Destroy all the Terraform Managed Resources

1. From a shell in your project folder (with your Account Information in environment) run:

   ```
    $ terraform destroy
   ```
1.  Accept the changes if they look appropriate.
1. Log in to the console to verify that all the objects are destroyed. The database, schema, warehouse, role, and the user objects created by Terraform will be automatically deleted.

### Drop the User we added

- From your Snowflake console run:

   ```SQL
   DROP USER "tf-snow";
   ```

## Conclusion
Duration: 3

If you are new to Terraform, there's still a lot to learn. We suggest researching [remote state](https://www.terraform.io/docs/language/state/remote.html), [input variables](https://www.terraform.io/docs/language/values/variables.html), and [building modules](https://www.terraform.io/docs/language/modules/develop/index.html). This will empower you to build and manage your Snowflake environment(s) through a simple declarative language.

The Terraform provider for Snowflake is an open-source project. If you need Terraform to manage a resource that has not yet been created in the [provider](https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest), we welcome contributions! We also welcome submitting issues and feedback to the [Github Project](https://github.com/SnowflakeLabs/terraform-provider-snowflake) to help improve the Terraform provider project and overall experience.

### Next steps

* You will need to decide how you will run your Terraform changes. In this demo, you ran everything on your local computer, but that is rarely done in a production environment. Best practices will have CI/CD pipelines that automate all workflows responsible for changing shared environments. CI/CD pipelines provide better gates for changing those environments, and they produce an audit trail in source control so that you can review the history of an environment.

* You will want to make the decision about how you isolate your environments and projects, whether via namespacing/RBAC or via multiple accounts. Changing this later is difficult as most modules and CI/CD infrastructure will need to be heavily modified for the alternative approach.

* You may also need to evaluate other tools to complete your infrastructure management. Terraform is a powerful tool for managing many resources in Snowflake, but it has limitations managing schema and data changes.

Other tools are available to manage things like data migrations and table schema changes. We often see Terraform paired with one of the following to meet all customer requirements.
- [dbt](https://www.getdbt.com/)
- [snowchange](https://github.com/Snowflake-Labs/snowchange)
- [Flyway](https://flywaydb.org/)


If you had any issues with this project you can pull [a working version](https://github.com/Snowflake-Labs/sfguide-terraform-sample) directly from Github.

### What we've covered
- Getting started with Terraform
- Setting up a new project
- Adding a new database, warehouse, schema, user, role, and new grants
- Cleaning up by destroying all the resources we created
