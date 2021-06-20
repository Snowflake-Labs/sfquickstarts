author: Adrian Lee
id: devops_dcm_schemachange_jenkins
summary: This guide will provide step-by-step details for getting started with DevOps on Snowflake by leveraging schemachange and Jenkins
categories: DevOps
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: DevOps, Data Engineering 

# DevOps: Database Change Management with schemachange and Jenkins
<!-- ------------------------ -->
## Overview 
Duration: 1

<img src="assets/devops_dcm_schemachange_jenkins-1.png" width="600" />

This guide will provide step-by-step instructions for how to build a simple CI/CD pipeline for Snowflake with Jenkins. My hope is that this will provide you with enough details to get you started on your DevOps journey with Snowflake and Jenkins.

DevOps is concerned with automating the development, release and maintenance of software applications. As such, DevOps is very broad and covers the entire Software Development Life Cycle (SDLC). The landscape of software tools used to manage the entire SDLC is complex since there are many different required capabilities/tools, including:

- Requirements management
- Project management (Waterfall, Agile/Scrum)
- Source code management (Version Control)
- Build management (CI/CD)
- Test management (CI/CD)
- Release management (CI/CD)

This guide will focus primarily on automated release management for Snowflake by leveraging the open-source Jenkins tool. Additionally, in order to manage the database objects/changes in Snowflake I will use the schemachange Database Change Management (DCM) tool.

Let’s begin with a brief overview of GitHub and Jenkins.

### Prerequisites

This guide assumes that you have a basic working knowledge of Git repositories.

### What You’ll Learn 
- A brief overview of Jenkins 
- A brief idea and overview of schemachange 
- How does schemachange help in database change management
- How does Jenkins help to create a pipeline for schemachange 
- How do we incorporate containers to easily run Jenkins and schemachange
- How do we have Jenkins serve as a "front-end" for on-demand requests

### What You’ll Need 

You will need the following things before beginning:

1. Snowflake
  1. **A Snowflake Account.**
  1. **A Snowflake Database named DEMO_DB.**
  1. **A Snowflake User created with appropriate permissions.** This user will need permission to create objects in the DEMO_DB database.
1. GitHub
  1. **A GitHub Account.** If you don’t already have a GitHub account you can create one for free. Visit the [Join GitHub](https://github.com/join) page to get started.
  1. **A GitHub Repository.** If you don't already have a repository created, or would like to create a new one, then [Create a new respository](https://github.com/new). For the type, select `Public` (although you could use either). And you can skip adding the README, .gitignore and license for now.
1. Integrated Development Environment (IDE)
  1. **Your favorite IDE with Git integration.** If you don’t already have a favorite IDE that integrates with Git I would recommend the great, free, open-source [Visual Studio Code](https://code.visualstudio.com/).
  1. **Your project repository cloned to your computer.** For connection details about your Git repository, open the Repository and copy the `HTTPS` link provided near the top of the page. If you have at least one file in your repository then click on the green `Code` icon near the top of the page and copy the `HTTPS` link. Use that link in VS Code or your favorite IDE to clone the repo to your computer.
1. Docker
  1. **Docker Desktop on your laptop.**  We will be running Jenkins as a container. Please install Docker Desktop on your desired OS by following the [Docker setup instructions](https://docs.docker.com/desktop/).

### What You’ll Build 

- A simple, working Jenkins pipeline service for Snowflake

<!-- ------------------------ -->
## Jenkins Overview
Duration: 2

<img src="assets/devops_dcm_schemachange_jenkins-2.png" width="250" />

### Jenkins
"Jenkins is a self-contained, open source automation server which can be used to automate all sorts of tasks related to building, testing, and delivering or deploying software" (from Jenkins' [Documentation](https://www.jenkins.io/doc/)).

Unlike other complete SDLC tools, Jenkins does not include built-in support for version control repositories or project management. Instead Jenkins is focused on CI/CD pipelines.

Negative
: **Note** - For this guide we will use GitHub for our Git repo.

<!-- ------------------------ -->
## schemachange Overview
Duration: 2

<img src="assets/devops_dcm_schemachange_jenkins-3.png" width="250" />

Database Change Management (DCM) refers to a set of processes and tools which are used to manage the objects within a database. It’s beyond the scope of this guide to provide details around the challenges with and approaches to automating the management of your database objects. If you’re interested in more details, please see my blog post [Embracing Agile Software Delivery and DevOps with Snowflake](https://www.snowflake.com/blog/embracing-agile-software-delivery-and-devops-with-snowflake/).

schemachange is a lightweight Python-based tool to manage all your Snowflake objects. It follows an imperative-style approach to database change management (DCM) and was inspired by [the Flyway database migration tool](https://flywaydb.org/). When schemachange is combined with a version control tool and a CI/CD tool, database changes can be approved and deployed through a pipeline using modern software delivery practices.

For more information about schemachange please see [the schemachange project page](https://github.com/Snowflake-Labs/schemachange).

Negative
: **Note** - schemachange is a community-developed tool, not an official Snowflake offering. It comes with no support or warranty.


<!-- ------------------------ -->
## Create Your First Database Migration
Duration: 4

Open up your cloned repository in your favorite IDE and create a folder named `migrations`. In that new folder create a script named `V1.1.1__initial_objects.sql` (make sure there are two underscores after the version number) with the following contents:

```sql
CREATE SCHEMA DEMO;
CREATE TABLE HELLO_WORLD
(
   FIRST_NAME VARCHAR
  ,LAST_NAME VARCHAR
);
```

Then commit the new script and push the changes to your GitHub repository. Assuming you started from an empty repository, your repository should look like this:

<img src="assets/devops_dcm_schemachange_jenkins-4.png" width="900" />

<!-- ------------------------ -->
## Deploying Jenkins
Duration: 5

### Building and Running a Docker Image

In order to deploy Jenkins we're going to create a Docker custom Docker image and then run it locally. So first, create a Docker file named ```Dockerfile``` in the root of your GitHub repository with the following contents: 

```
FROM jenkins/jenkins:lts

# Install required applications
USER root
RUN apt-get update
RUN apt-get install -y docker.io

# Drop back to the regular jenkins user
USER jenkins
```

Next, to create the custom Docker image run the following command from a shell:

```
docker build -t jenkins .
```

After the Docker image has been created we can then create and run a container based on that image. This will start up a Jenkins container locally:

```
docker run -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --name jenkins \
  jenkins
```

Positive
: **Tip** - Please note that the initial admin password for your Jenkins installation will be printed out in the Docker output. So please copy it for use later in this step.

The last thing we need to do, once the Jenkins container is running, is to give Jenkins access to the Docker engine by running this command:

```
docker exec -it -u root jenkins bash -c 'chmod 666 /var/run/docker.sock'
```

### Configuring Jenkins

To access the Jenkins UI, open ```localhost:8080``` in a new tab in your web browser of choice. The first getting started screen titled "Unlock Jenkins" will ask you to enter the admin passowrd. This is password mentioned above that you copied and saved. Enter the password and click ```Next```.

Next you will see the "Customize Jenkins" set up screen. Click on the ```Install suggested plugins``` button as shown below and wait for all the suggested plugins to be installed.

<img src="assets/devops_dcm_schemachange_jenkins-5.png" width="900" />

After all the plugins have been installed you will be taken to the "Create First Admin User" page. Enter ```admin``` for the "Username" (and "Full name"), enter a password which will be used the Jenkins admin user, and enter a valid email address. Confirm that your screen looks like the image below (with the exception that you entered an email address) and then click on the ```Save and Continue``` button.

<img src="assets/devops_dcm_schemachange_jenkins-6.png" width="900" />

On the final getting started set up screen, leave the "Instance Configuration" Jenkins URL as ```http://localhost:8080```. Then click on the ```Save and Finish``` button and then on the ```Start using Jenkins``` button.

You should now be at the main Jenkins Dashobard page and ready to start using Jenkins. If you find yourself at a login page (like below) then enter the admin user credentials and click ```Sign in```.

<img src="assets/devops_dcm_schemachange_jenkins-8.png" width="900" />

That last thing we need to do in order to set up Jenkins for this guide is to install the Docker Pipeline plugin in Jenkins. This plugin allows Jenkins Pipeline Projects to build and test using Docker images.

Click on ```Manage Jenkins``` in the left navigation bar and then on the ```Manage Plugins``` under "System Configuration".

<img src="assets/devops_dcm_schemachange_jenkins-9.png" width="900" />

From the Plugin Manager click on the "Available" tab and enter ```docker pipeline``` in the search box. You should see one result called "Docker Pipeline". Check the box under this "Install" column next to this plugin and then click on the ```Install without restart``` button:

<img src="assets/devops_dcm_schemachange_jenkins-10.png" width="900" />

On the next results page you should see a bunch of green checkmarks each with a "Success" status. Click on the ```Go back to the top page``` link to return to the main Jenkins Dashboard page. And with that Jenkins is set up and ready to use!

<!-- ------------------------ -->
## Configuring Jenkins pipeline

Login and we are now ready to set up our pipeline in Jenkins. 

First, let us set up our Jenkinsfile and commit to our repository. Toggle back to you IDE and create a Jenkinsfile and place the code below in a file entitled ```Jenkinsfile```

```
pipeline {
    agent { 
        docker { 
            image "python:3.7"
            args '--user 0:0'
        } 
        
    }
    environment {
       SNOWFLAKE_PASSWORD="${SNOWFLAKE_PASSWORD}"
       ROOT_FOLDER="${ROOT_FOLDER}"
       SNOWFLAKE_ACCOUNT="${SNOWFLAKE_ACCOUNT}"
       SNOWFLAKE_USER="${SNOWFLAKE_USER}"
       SNOWFLAKE_ROLE="${SNOWFLAKE_ROLE}"
       SNOWFLAKE_WAREHOUSE="${SNOWFLAKE_WAREHOUSE}"
       SNOWFLAKE_METADATACHANGE="${SNOWFLAKE_METADATACHANGE}"
   }    
    stages {

        stage('Deploying Schemachange') {
            steps {
                sh "pip install schemachange --upgrade && schemachange -f $ROOT_FOLDER -a $SNOWFLAKE_ACCOUNT -u $SNOWFLAKE_USER -r $SNOWFLAKE_ROLE -w $SNOWFLAKE_WAREHOUSE -c $SNOWFLAKE_METADATACHANGE"
            }
        }
    }
}
```

Commit your code to GitHub. It should look like this. 

<img src="assets/devops_dcm_schemachange_jenkins-12.png" width="900" />

Now take note of your repository url. You can find it under the code button as indicated in the image below. 

<img src="assets/devops_dcm_schemachange_jenkins-13.png" width="900" />

We are ready to set up our Jenkins pipeline in the Jenkins console. To do so, go to ```localhost:8080``` login and create a new pipeline item. We will name this pipeline item as ```schema-jenkins-demo```

<img src="assets/devops_dcm_schemachange_jenkins-14.png" width="900" />

Click on ```configure``` and then on the option ```this project is parameterised```. Click on ```Add Paramter``` and follow the table for the corresponding paramter type, Name and Parameter Type. Leave the ROOT_FOLDER as migrations and the SNOWFLAKE_METADATCHANGE as DEMO_DB.SCHEMACHANGE.CHANGE_HISTORY

<img src="assets/devops_dcm_schemachange_jenkins-15.png" width="900" />

<table>
    <thead>
        <tr>
            <th>Parameter Type</th>
            <th>Parameter name</th>
            <th>Parameter value</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>String Parameter</td>
            <td>SNOWFLAKE_ACCOUNT</td>
            <td>xy12345.apsoutheast-1</td>
        </tr>
        <tr>
            <td>String Parameter</td>
            <td>SNOWFLAKE_USER</td>
            <td>DEMO_USER</td>
        </tr>
        <tr>
            <td>Password Parameter</td>
            <td>SNOWFLAKE_PASSWORD</td>
            <td>*****</td>
        </tr>
        <tr>
            <td>String Parameter</td>
            <td>SNOWFLAKE_ROLE</td>
            <td>DEMO_ROLE</td>
        </tr>
        <tr>
            <td>String Parameter</td>
            <td>SNOWFLAKE_WAREHOUSE</td>
            <td>DEMO_WH</td>
        </tr>
        <tr>
            <td>String Parameter</td>
            <td>ROOT_FOLDER</td>
            <td>migrations</td>
        </tr>
        <tr>
            <td>String Parameter</td>
            <td>SNOWFLAKE_METADATACHANGE</td>
            <td>DEMO_DB.SCHEMACHANGE.CHANGE_HISTORY</td>
        </tr>
    </tbody>
</table>

A sample of a parameter configuration in the Jenkins console is shown in the image below

<img src="assets/devops_dcm_schemachange_jenkins-16.png" width="900" />

Under the ```Pipeline``` section for Definition, choose ```Pipeline script from SCM``` and then choose ```Git``` under SCM. Input the repository url that we had noted above. Click advanced and for the enter the items for the below parameters

1) Name: ```origin```

2) Refspec: ```+refs/pull/*:refs/remotes/origin/pr/*```

3) Branches to build : leave blank

4) Script Path : ```Jenkinsfile```

5) Uncheck lightweight checkout

If all is good, it should look like this

<img src="assets/devops_dcm_schemachange_jenkins-17.png" width="900" />


Positive
: **Tip** - If you are using a private GitHub repository, then you would need to input your credentials to your GitHub repository. If not you can just leave the credentials as blank. 

Positive
: **Tip** - I have attached my repsitory here in case you want a [reference](https://github.com/sfc-gh-adlee/snowflake_devops_schemachange_public.git).  

<!-- ------------------------ -->
## Running our Jenkins pipeline

We are now ready to run our Jenkins pipeline. To run the pipeline, click on the ```schema-jenkins-demo``` pipeline and then hit ```build with parameters``` as seen in the image below. 

<img src="assets/devops_dcm_schemachange_jenkins-18.png" width="900" />

If all goes well, you should see a successful output that indicates the build was successful

<img src="assets/devops_dcm_schemachange_jenkins-19.png" width="900" />

Let us go over to our snowflake portal and you can see that the table ```hello_world``` has been created!

<img src="assets/devops_dcm_schemachange_jenkins-20.png" width="900" />

Positive
: **Tip** - As we have deployed Jenkins on a localhost environment, we are not able to configure push and pull requests because it isn't reachable over the public Internet. However, if you choose to deploy in an instance where it is publicly accessible (say in AWS, Azure or GCP), you can follow this guide to configure a GitHub hook trigger for [GITScm] (https://www.blazemeter.com/blog/how-to-integrate-your-github-repository-to-your-jenkins-project)

<!-- ------------------------ -->
## Running a new change in our table with Jenkins pipeline

Now let's introduce a new change into our table. We are going to add in a new column (```middle_name```) into the ```hello_world``` table  we created above. 

Create a new file in the ```migrations``` folder entitled ```V1.1.2__updated_objects.sql.sql```.

Inside ```V1.1.2__updated_objects.sql.sql```, paste in the below sql statement and commit your code. 

```sql
USE DATABASE DEMO_DB;
USE SCHEMA DEMO_DB.DEMO;

// create the table hello_world
ALTER TABLE HELLO_WORLD ADD COLUMN MIDDLE_NAME VARCHAR;

```
Your migrations folder should look like this as shown below. 

<img src="assets/devops_dcm_schemachange_jenkins-21.png" width="900" />

Now, toggle back to the Jenkins url and trigger the pipeline again. You will see that the table has been updated successfully to include in the new column.  



<!-- ------------------------ -->
## Conclusion & Next Steps
Duration: 4

So now that you’ve got your Snowflake CI/CD pipeline set up with Jenkins - one of the most popular open source CI/CD tooling. The software development life cycle, including CI/CD pipelines, gets much more complicated in the real-world. Best practices include pushing changes through a series of environments, adopting a branching strategy, and incorporating a comprehensive testing strategy, to name a few.

#### Pipeline Stages
In the real-world you will have multiple stages in your build and release pipelines. A simple, helpful way to think about stages in a deployment pipeline is to think about them as environments, such as dev, test, and prod. With Jenkins, you can create different pipelines for the corresponding branches as referenced [here](https://www.jenkins.io/doc/book/pipeline/multibranch/).

#### Branching Strategy
Branching strategies can be complex, but there are a few popular ones out there that can help get you started. To begin with I would recommend keeping it simple with [GitHub flow](https://guides.github.com/introduction/flow/) (and see also [an explanation of GitHub flow by Scott Chacon in 2011](http://scottchacon.com/2011/08/31/github-flow.html)). Another simple framework to consider is [GitLab flow](https://about.gitlab.com/blog/2014/09/29/gitlab-flow/).

#### Testing Strategy
Testing is an important part of any software development process, and is absolutely critical when it comes to automated software delivery. But testing for databases and data pipelines is complicated and there are many approaches, frameworks, and tools out there. In my opinion, the simplest way to get started testing data pipelines is with [dbt](https://www.getdbt.com/) and the [dbt Test features](https://docs.getdbt.com/docs/building-a-dbt-project/tests/). Another popular Python-based testing tool to consider is [Great Expectations](https://greatexpectations.io/).

With that you should now have a working CI/CD pipeline in Jenkins and some helpful ideas for next steps on your DevOps journey with Snowflake. Good luck!

### What We've Covered

* A brief history and overview of Jenkins
* A brief history and overview of schemachange
* How database change management tools like schemachange work
* How a simple release pipeline works
* How to create CI/CD pipelines in Jenkins
* Ideas for more advanced CI/CD pipelines with stages
* How to get started with branching strategies
* How to get started with testing strategies

### Related Resources

* [schemachange](https://github.com/Snowflake-Labs/schemachange)
* [Jenkins Pipelines](https://www.jenkins.io/doc/book/pipeline/)