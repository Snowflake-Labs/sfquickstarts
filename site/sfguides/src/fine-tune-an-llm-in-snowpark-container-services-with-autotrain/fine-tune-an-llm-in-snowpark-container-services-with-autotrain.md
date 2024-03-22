author: Jason Summer
id: fine-tune-an-llm-in-snowpark-container-services-with-autotrain
summary: Fine-Tuning an LLM in Snowpark Container Services with AutoTrain
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Science, LLM, AI 

# Fine-Tuning an LLM in Snowpark Container Services with AutoTrain
<!-- ------------------------ -->
## Overview 
Duration: 5

By completing this guide, you will fine-tune an open-source Large Language Model (LLM) in Snowpark Container Services using HuggingFace's AutoTrain-Advanced module. The result will be an LLM further trained to understand and describe raw product metadata.

Here is a summary of what you will be able to learn in each step by following this quickstart:

- **Environment Setup**: Establish Snowflake objects, roles, grants, and SnowCLI for Snowpark Container Services
- **Training Data**: Format and load example training into Snowflake stage
- **Service Image & Spec**: Construct, build, and push a docker image and spec file to Snowflake
- **Container Service**: Start a Snowpark Container Service and monitor its status
- **LLM Prompting**: Start a web server to chat with the fine-tuned (and base) LLM

In case you are new to some of the technologies mentioned above, here’s an overview with links to documentation.

Through this quickstart guide, you will use [Snowpark Container Services](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview), which are now in Public Preview on AWS and Private Preview on Azure and Google Cloud. **Please note: this quickstart assumes some existing knowledge and familiarity with containerization (e.g. Docker) and basic familiarity with container orchestration.**

### What is Snowpark Container Services?

![Snowpark Container Service](./assets/containers.png)

[Snowpark Container Services](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview) is a fully managed container offering that allows you to easily deploy, manage, and scale containerized services, jobs, and functions, all within the security and governance boundaries of Snowflake, and requiring zero data movement. As a fully managed service, SPCS comes with Snowflake’s native security, RBAC support, and built-in configuration and operational best-practices.

Snowpark Container Services are fully integrated with both Snowflake features and third-party tools, such as Snowflake Virtual Warehouses and Docker, allowing teams to focus on building data applications, and not building or managing infrastructure. Just like all things Snowflake, this managed service allows you to run and scale your container workloads across regions and clouds without the additional complexity of managing a control plane, worker nodes, and also while having quick and easy access to your Snowflake data.

The introduction of Snowpark Container Services on Snowflake includes the incorporation of new object types and constructs to the Snowflake platform, namely: images, image registry, image repositories, compute pools, specification files, services, and jobs.

For more information on these objects, check out [this article](https://medium.com/snowflake/snowpark-container-services-a-tech-primer-99ff2ca8e741) along with the Snowpark Container Services [documentation](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview).

Note that while in this quickstart, we will predominantly use the direct SQL commands to interact with Snowpark Container Services and their associated objects, there is also [Python API support](https://docs.snowflake.com/developer-guide/snowflake-python-api/snowflake-python-overview) in Public Preview that you can also use. Refer to the [documentation](https://docs.snowflake.com/developer-guide/snowflake-python-api/snowflake-python-overview) for more info.

### What is Fine-Tuning?

Out of the box, LLMs can comprehend natural language but tend to fall short in use cases that require additional context, behavior, or tone. While context or specific instructions can be dynamically passed to the LLM, the amount of context, knowledge, or instruction may exceed the context window of a given LLM. In such cases, fine-tuning, or training a model on input-output pairs can be considered. As a simplified example, we will be fine-tuning an LLM to understand product metadata in its raw form.

### What is AutoTrain-Advanced?

![add HG LOGO](./assets/hf.png)

Fine-tuning can be a rather complex process. To alleviate much of this complexity, we will be running HuggingFace's AutoTrain-Advanced Python package in the containerized service to securely fine-tune an LLM using Snowflake compute. Refer to the [documentation](https://huggingface.co/docs/autotrain/index) for more info.

### What you will learn 
- The basic mechanics of how Snowpark Container Services works
- How to deploy a long-running service with a UI and use volume mounts to persist LLMs in the file system
- How to fine-tune an LLM with HuggingFace's AutoTrain-Advanced modules
- How to deploy a LLM chat-interface with FastChat (optional)

### Prerequisites

- Download the git repo here: [add git repo]. You can simply download the repo as a .zip if you don't have Git installed locally.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- [HuggingFace Token](https://huggingface.co/docs/hub/en/security-tokens)
- (Optional) [VSCode](https://code.visualstudio.com/) (recommended) with the [Docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker) and [Snowflake](https://marketplace.visualstudio.com/items?itemName=snowflake.snowflake-vsc) extensions installed.
- (Optional) [SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql-install-config) or [SnowCLI](https://github.com/snowflakedb/snowflake-cli) installed and configured for Snowflake account.
- A non-trial Snowflake account in a supported [AWS region](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview#available-regions).
- A Snowflake account login with a role that has the `ACCOUNTADMIN` role. If not, you will need to work with your `ACCOUNTADMIN` to perform the initial account setup (e.g. creating the `CONTAINER_USER_ROLE` and granting required privileges, as well as creating the OAuth Security Integration).

<!-- ------------------------ -->
## Setup Environment
Duration: 5

> aside positive
> IMPORTANT: The Snowflake environment setup that follows is the same as the setup in [Quickstart: Intro to Snowpark Container Services](https://quickstarts.snowflake.com/guide/intro_to_snowpark_container_services/index.html#1). However, here we create a GPU-powered compute pool. You will only need to complete the Setup Environment section once but ensure you have a `GPU_NV_M` instance compute pool.

Run the following SQL commands in [`00_setup.sql`](https://github.com/Snowflake-Labs/sfguide-intro-to-snowpark-container-services/blob/main/00_setup.sql) using the Snowflake VSCode Extension OR in a SQL worksheet to create the role, database, warehouse, and stage that we need to get started:
```SQL
// Create an CONTAINER_USER_ROLE with required privileges
USE ROLE ACCOUNTADMIN;
CREATE ROLE CONTAINER_USER_ROLE;
GRANT CREATE DATABASE ON ACCOUNT TO ROLE CONTAINER_USER_ROLE;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE CONTAINER_USER_ROLE;
GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE CONTAINER_USER_ROLE;
GRANT CREATE INTEGRATION ON ACCOUNT TO ROLE CONTAINER_USER_ROLE;
GRANT MONITOR USAGE ON ACCOUNT TO  ROLE  CONTAINER_USER_ROLE;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE CONTAINER_USER_ROLE;
GRANT IMPORTED PRIVILEGES ON DATABASE snowflake TO ROLE CONTAINER_USER_ROLE;

// Grant CONTAINER_USER_ROLE to ACCOUNTADMIN
grant role CONTAINER_USER_ROLE to role ACCOUNTADMIN;

// Create Database, Warehouse, and Image spec stage
USE ROLE CONTAINER_USER_ROLE;
CREATE OR REPLACE DATABASE CONTAINER_HOL_DB;

CREATE OR REPLACE WAREHOUSE CONTAINER_HOL_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 120
  AUTO_RESUME = TRUE;
  
CREATE STAGE IF NOT EXISTS specs
ENCRYPTION = (TYPE='SNOWFLAKE_SSE');

CREATE STAGE IF NOT EXISTS volumes
ENCRYPTION = (TYPE='SNOWFLAKE_SSE')
DIRECTORY = (ENABLE = TRUE);
```

Run the following SQL commands in [`01_snowpark_container_services_setup.sql`](https://github.com/Snowflake-Labs/sfguide-intro-to-snowpark-container-services/blob/main/01_snowpark_container_services_setup.sql) using the Snowflake VSCode Extension OR in a SQL worksheet to create the [OAuth Security Integration](https://docs.snowflake.com/en/user-guide/oauth-custom#create-a-snowflake-oauth-integration), [External Access Integration](https://docs.snowflake.com/developer-guide/snowpark-container-services/additional-considerations-services-jobs#network-egress) our first [compute pool](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/working-with-compute-pool), and our [image repository](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/working-with-registry-repository)
```SQL
USE ROLE ACCOUNTADMIN;
CREATE SECURITY INTEGRATION IF NOT EXISTS snowservices_ingress_oauth
  TYPE=oauth
  OAUTH_CLIENT=snowservices_ingress
  ENABLED=true;

CREATE OR REPLACE NETWORK RULE ALLOW_ALL_RULE
  TYPE = 'HOST_PORT'
  MODE = 'EGRESS'
  VALUE_LIST= ('0.0.0.0:443', '0.0.0.0:80');

CREATE EXTERNAL ACCESS INTEGRATION ALLOW_ALL_EAI
  ALLOWED_NETWORK_RULES = (ALLOW_ALL_RULE)
  ENABLED = true;

GRANT USAGE ON INTEGRATION ALLOW_ALL_EAI TO ROLE CONTAINER_USER_ROLE;

USE ROLE CONTAINER_USER_ROLE;
CREATE COMPUTE POOL IF NOT EXISTS CONTAINER_HOL_POOL
MIN_NODES = 1
MAX_NODES = 1
INSTANCE_FAMILY = GPU_NV_M
AUTO_RESUME = true;

CREATE IMAGE REPOSITORY CONTAINER_HOL_DB.PUBLIC.IMAGE_REPO;

SHOW IMAGE REPOSITORIES IN SCHEMA CONTAINER_HOL_DB.PUBLIC;
```
- The [OAuth security integration](https://docs.snowflake.com/en/user-guide/oauth-custom#create-a-snowflake-oauth-integration) will allow us to login to our UI-based services using our web browser and Snowflake credentials
- The [External Access Integration](https://docs.snowflake.com/developer-guide/snowpark-container-services/additional-considerations-services-jobs#network-egress) will allow our services to reach outside of Snowflake to the public internet
- The [compute pool](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/working-with-compute-pool) is the set of compute resources on which our services will run
- The [image repository](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/working-with-registry-repository) is the location in Snowflake where we will push our Docker images so that our services can use them

> aside positive
> IMPORTANT: If you use different names for objects created in this section, be sure to update scripts and code in the following sections accordingly.

<!-- ------------------------ -->
## Metadata Configuration
Duration: 2

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:


- **summary**: This is a sample Snowflake Guide 
  - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
- **id**: fine-tune-an-llm-in-snowpark-container-services-with-autotrain
  - make sure to match the id here with the name of the file, all one word.
- **categories**: data-science 
  - You can have multiple categories, but the first one listed is used for the icon.
- **environments**: web 
  - `web` is default. If this will be published for a specific event or  conference, include it here.
- **status**: Published
  - (`Draft`, `Published`, `Deprecated`, `Hidden`) to indicate the progress and whether the sfguide is ready to be published. `Hidden` implies the sfguide is for restricted use, should be available only by direct URL, and should not appear on the main landing page.
- **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
- **tags**: Data Science, LLM, AI
  - Add relevant  tags to make your sfguide easily found and SEO friendly.
- **authors**: Jason Summer
  - Indicate the author(s) of this specific sfguide.

---

You can see the source metadata for this guide you are reading now, on [the github repo](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md).


<!-- ------------------------ -->
## Creating a Step
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

All the content for the step goes here.

## Step 2 Title
Duration: 1

All the content for the step goes here.
```

To indicate how long each step will take, set the `Duration` under the step title (i.e. `##`) to an integer. The integers refer to minutes. If you set `Duration: 4` then a particular step will take 4 minutes to complete. 

The total sfguide completion time is calculated automatically for you and will be displayed on the landing page. 

<!-- ------------------------ -->
## Code Snippets, Info Boxes, and Tables
Duration: 2

Look at the [markdown source for this sfguide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate code snippets, info boxes, and download buttons. 

### JavaScript
```javascript
{ 
  key1: "string", 
  key2: integer,
  key3: "string"
}
```

### Java
```java
for (statement 1; statement 2; statement 3) {
  // code block to be executed
}
```

### Info Boxes
> aside positive
> 
>  This will appear in a positive info box.


> aside negative
> 
>  This will appear in a negative info box.

### Buttons
<button>

  [This is a download button](link.com)
</button>

### Tables
<table>
    <thead>
        <tr>
            <th colspan="2"> **The table header** </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>The table body</td>
            <td>with two columns</td>
        </tr>
    </tbody>
</table>

### Hyperlinking
[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)

<!-- ------------------------ -->
## Images, Videos, and Surveys, and iFrames
Duration: 2

Look at the [markdown source for this guide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate these elements. 

### Images
![Puppy](assets/SAMPLE.jpg)

### Videos
Videos from youtube can be directly embedded:
<video id="KmeiFXrZucE"></video>

### Inline Surveys
<form>
  <name>How do you rate yourself as a user of Snowflake?</name>
  <input type="radio" value="Beginner">
  <input type="radio" value="Intermediate">
  <input type="radio" value="Advanced">
</form>

### Embed an iframe
![https://codepen.io/MarioD/embed/Prgeja](https://en.wikipedia.org/wiki/File:Example.jpg "Try Me Publisher")

<!-- ------------------------ -->
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What we've covered
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files