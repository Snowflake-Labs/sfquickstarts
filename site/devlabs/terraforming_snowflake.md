summary: Learn how to manage Snowflake using Terraform
id: terraforming_snowflake
categories: Getting Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/devlabs/issues
tags: Getting Started, Data Science, Data Engineering, Data Applications, Terraform
authors: Brad Culberson

# Terraforming Snowflake

## Overview
Duration: 5

[Terraform](https://www.terraform.io/) is an open-source Infrastructure as Code (IaC) tool created by HashiCorp. A [provider](https://registry.terraform.io/providers/chanzuckerberg/snowflake/latest/docs) is available for Snowflake (written by the [Chan Zuckerberg Initiative](https://chanzuckerberg.com/)), as well as the cloud providers we host on: [Azure](https://registry.terraform.io/providers/hashicorp/azurerm/latest), [AWS](https://registry.terraform.io/providers/hashicorp/aws/latest/docs), and [GCP](https://registry.terraform.io/providers/hashicorp/google/latest).

Terraform is declarative, so you can define the resources and configurations you want, and Terraform calculates dependencies, looks at previous state, and makes all the necessary changes to converge to the new desired state. Using Terraform is a great way to deploy new projects and make infrastructure changes in production. It makes managing dependencies between cloud providers especially easy.

Example Terraform use-cases:
 - Set up storage in your cloud provider and add it to Snowflake as an external stage
 - Add storage and connect it to Snowpipe
 - Create a service user and push the key into the secrets manager of your choice, or rotate keys

Many Snowflake customers use IaC to abide by compliance controls, maintain consistency, and support similar engineering workflows for infrastructure while updates are underway.

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

[Create](https://github.com/new) a new repository to hold your Terraform project. We use the name `tf-snow` in this lab. Here are the commands to use if you use the git command-line client:

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

Positive
: **Tip** – If the commands don't work, verify that you can connect to GitHub using your SSH key, and that your git config is correct for your account.

You now have an empty repo that we will use in subsequent steps to Terraform your Snowflake account.




## Create a Service User for Terraform
Duration: 5

We will now create a user account separate from your own that uses key-pair authentication. The reason this is required in this lab is due to the provider's limitations around caching credentials and the lack of support for 2FA. Service accounts and key pair are also how most CI/CD pipelines run Terraform.

### Create an RSA key for Authentication

This creates the private and public keys we use to authenticate the service account we will use
for Terraform.

```Shell
$ cd ~/.ssh
$ openssl genrsa -out snowflake_tf_snow_key 4096
$ openssl rsa -in snowflake_tf_snow_key -pubout -out snowflake_tf_snow_key.pub
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

Negative
: We grant the user `SYSADMIN` and `SECURITYADMIN` privileges to keep the lab simple. An important security best practice, however, is to limit all user accounts to least-privilege access. In a production environment, this key should also be secured with a secrets management solution like Hashicorp Vault, Azure Key Vault, or AWS Secrets Manager.

## Setup Terraform Authentication
Duration: 1

We need to pass provider information via environment variables and input variables so that Terraform can authenticate as the user.

Run the following to find the `YOUR_SNOWFLAKE_ACCOUNT_HERE` and `YOUR_SNOWFLAKE_REGION_HERE` values needed by the Snowflake console:

```SQL
SELECT current_account(), current_region();
```

### Add Account Information to Environment

Run these commands in your shell. Be sure to replace the `YOUR_SNOWFLAKE_ACCOUNT_HERE` and `YOUR_SNOWFLAKE_REGION_HERE` placeholders with the correct values.

```Shell
$ export SNOWFLAKE_USER="tf-snow"
$ export SNOWFLAKE_PRIVATE_KEY_PATH="~/.ssh/snowflake_tf_snow_key"
$ export SNOWFLAKE_ACCOUNT="YOUR_SNOWFLAKE_ACCOUNT_HERE"
$ export SNOWFLAKE_REGION="YOUR_SNOWFLAKE_REGION_HERE"
```

If you plan on working on this or other projects in multiple shells, it may be convenient to put this in a `snow.env` file that you can source or put it in your `.bashrc` or `.zshrc` file. For this lab, we expect you to run future Terraform commands in a shell with those set.

## Declaring Resources
Duration: 3

Add a file to your project in the base directory named `main.tf`. In `main.tf` we set up the provider and define the configuration for the database and the warehouse that we want Terraform to create.

Copy the contents of the following block to your `main.tf`

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

To set up the project to run Terraform, you first need to initialize the project.

Run the following from a shell in your project folder:

```Shell
$ terraform init
```

The dependencies needed to run Terraform are downloaded to your computer.

In this demo, we use local state for Terraform. The state files are required to calculate all changes. Because the files are needed to correctly merge future changes, they are extremely important. If multiple users run Terraform, and/or if it runs on different computers, and/or if runs through CI/CD, the state files' state **needs** to be put in [Remote Storage](https://www.terraform.io/docs/language/state/remote.html). While using local state, you'll see the current state stored in `*.tfstate` and old versions named `*.tfstate.*`.

The `.terraform` folder is where all dependencies are downloaded. It's safe to add _that_ and the state files to `.gitignore` to minimize changes.

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

To manage different environments (dev/test/prod), you can use names to isolate resources from one another, or—to reduce complexity and limit the blast radius—you can use separate Snowflake accounts. If you pass the environment as an [input variable](https://www.terraform.io/docs/language/values/variables.html) to the project, you can run the same Terraform project unchanged for each environment.

Your specific workflow will depend on your requirements, including your compliance needs, your other workflows, and your environment and account topology.

For this lab, you can simulate the proposed CI/CD job and do a plan to see what Terraform wants to change. During plan, Terraform compares its known and stored state with what's in the desired resources, and displays all changes needed to conform the resources.

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
1. Terraform recreates the plan and applies the needed changes after you verify it. In this case, Terraform will be creating two new resources, and have no other changes.

1. Log in to your Snowflake account and verify that Terraform created the database and the warehouse.


## Changing and Adding Resources
Duration: 5


All databases need a schema to store tables, so we'll add that and a service user so that our application/client can connect to the database and schema. The syntax is very similar to the database and warehouse you already created. By now you have learned everything you need to know to create and update resources in Snowflake. We'll also add privileges so the service role/user can use the database and schema.

You'll see that most of this is what you would expect. The only complicated part is creating the private key. Because the Terraform TLS private key generator doesn't export the public key in a format that the Terraform provider can consume, some string manipulations are needed.

1. Change the warehouse size in the `main.tf` file from `xsmall` to `small`.

1. Add the following resources to your `main.tf` file:

   ```
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

1. To get the public and private key information for the application, use Terraform [output variables](https://www.terraform.io/docs/language/values/outputs.html).

    Add the following resources to a new file named `outputs.tf`

    ```
    output "snowflake_svc_public_key" {
        value = tls_private_key.svc_key.public_key_pem
    }

    output "snowflake_svc_private_key" {
        value = tls_private_key.svc_key.private_key_pem
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

You can log in to Github to create the Pull Request and merge the changes.

## Apply and Verify the Changes
Duration: 2

To simulate the CI/CD pipeline, we can apply the changes to conform the desired state with the stored state.

1. From a shell in your project folder (with your Account Information in environment) run:

   ```
   $ terraform apply
   ```

1. Accept the changes if they look appropriate.
1. Log in to the console to see all the changes complete.

Because all changes are stored in source control and applied by CI/CD, you can get a history of all your environment changes. You can  put compliance controls into place and limit authorization to directly manage the environments to fewer users. But this also makes it easy to bring up new environments that are identical to others in a timely manner without managing SQL scripts.

## Cleanup
Duration: 1

You're almost done with the demo. We have one thing left to do: clean up your account.

### Destroy all the Terraform Managed Resources

1. From a shell in your project folder (with your Account Information in environment) run:

   ```
    $ terraform destroy
   ```
   Accept the changes if they look appropriate.
1. Log in to the console to verify that all the objects are destroyed.

### Drop the User we added

1. From your Snowflake console run:

   ```SQL
   DROP USER "tf-snow";
   ```

## Conclusion
Duration: 3

If you are new to Terraform, there's still a lot to learn. We suggest researching [remote state](https://www.terraform.io/docs/language/state/remote.html), [input variables](https://www.terraform.io/docs/language/values/variables.html), and [building modules](https://www.terraform.io/docs/language/modules/develop/index.html). This will empower you to build and manage your Snowflake environment(s) through a simple declarative language.

The Terraform provider for Snowflake is an open-source project. If you need Terraform to manage a resource that has not yet been created in the [provider](https://registry.terraform.io/providers/chanzuckerberg/snowflake/latest), we welcome contributions! We also welcome submitting issues and feedback to the [Github Project](https://github.com/chanzuckerberg/terraform-provider-snowflake) to help improve the Terraform provider project and overall experience.

### Next steps

* You will need to decide how you will run your Terraform changes. In this demo, you ran everything on your local computer, but that is rarely done in a production environment. Best practices will have CI/CD pipelines that automate all workflows responsible for changing shared environments. CI/CD pipelines provide better gates for changing those environments, and they produce an audit trail in source control so that you can review the history of an environment.

* You will want to make the decision about how you isolate your environments and projects, whether via namespacing/RBAC or via multiple accounts. Changing this later is difficult as most modules and CI/CD infrastructure will need to be heavily modified for the alternative approach.

* You may also need to evaluate other tools to complete your infrastructure management. Terraform is a powerful tool for managing many resources in Snowflake, but it has limitations managing schema and data changes. More robust tools are available to manage things like data migrations and table schema changes.

If you had any issues with this project you can pull [a working version](https://github.com/Snowflake-Labs/sfguide-terraform-sample) directly from Github.

### What we've covered
- Getting started with Terraform
- Setting up a new project
- Adding a new database, warehouse, schema, user, role, and new grants
- Cleaning up by destroying all the resources we created
