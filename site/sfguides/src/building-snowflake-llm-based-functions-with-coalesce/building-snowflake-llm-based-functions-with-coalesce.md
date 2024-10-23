author: Josh Hall
id: building-snowflake-llm-based-functions-with-coalesce
summary: Learn to build Cortex based data pipelines in Coalesce
categories: data-engineering
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Engineering, Getting Started

# Snowflake Guide Template
<!-- ------------------------ -->
## Overview 
Duration: 1

Please use [this markdown file](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) as a template for writing your own Snowflake Quickstarts. This example guide has elements that you will use when writing your own guides, including: code snippet highlighting, downloading files, inserting photos, and more. 

It is important to include on the first page of your guide the following sections: Prerequisites, What you'll learn, What you'll need, and What you'll build. Remember, part of the purpose of a Snowflake Guide is that the reader will have **built** something by the end of the tutorial; this means that actual code needs to be included (not just pseudo-code).

The rest of this Snowflake Guide explains the steps of writing your own guide. 

### Prerequisites
- Familiarity with Markdown syntax

### What You’ll Learn 
- how to set the metadata for a guide (category, author, id, etc)
- how to set the amount of time each slide will take to finish 
- how to include code snippets 
- how to hyperlink items 
- how to include images 

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- [VSCode](https://code.visualstudio.com/download) Installed
- [NodeJS](https://nodejs.org/en/download/) Installed
- [GoLang](https://golang.org/doc/install) Installed

### What You’ll Build 
- A Snowflake Guide

<!-- ------------------------ -->
## Setup Work
To complete this lab, please create free trial accounts with Snowflake and Coalesce by following the steps below. You have the option of setting up Git-based version control for your lab, but this is not required to perform the following exercises. Please note that none of your work will be committed to a repository unless you set Git up before developing.

We recommend using Google Chrome as your browser for the best experience.

| Note: Not following these steps will cause delays and reduce your time spent in the Coalesce environment\! |
| :---- |

### Step 1: Create a Snowflake Trial Account  

1. Fill out the Snowflake trial account form [here](https://signup.snowflake.com/?utm_source=google&utm_medium=paidsearch&utm_campaign=na-us-en-brand-trial-exact&utm_content=go-eta-evg-ss-free-trial&utm_term=c-g-snowflake%20trial-e&_bt=579123129595&_bk=snowflake%20trial&_bm=e&_bn=g&_bg=136172947348&gclsrc=aw.ds&gclid=Cj0KCQiAtvSdBhD0ARIsAPf8oNm6YH7UeRqFRkVeQQ-3Akuyx2Ijzy8Yi5Om-mWMjm6dY4IpR1eGvqAaAg3MEALw_wcB). Use an email address that is not associated with an existing Snowflake account.   
     
2. When signing up for your Snowflake account, select the region that is physically closest to you and choose Enterprise as your Snowflake edition. Please note that the Snowflake edition, cloud provider, and region used when following this guide do not matter.   
  


3. After registering, you will receive an email from Snowflake with an activation link and URL for accessing your trial account. Finish setting up your account following the instructions in the email. 

### Step 2: Create a Coalesce Trial Account with Snowflake Partner Connect 

Once you are logged into your Snowflake account, sign up for a free Coalesce trial account using Snowflake Partner Connect. Check your Snowflake account profile to make sure that it contains your fist and last name. 

Once you are logged into your Snowflake account, sign up for a free Coalesce trial account using Snowflake Partner Connect. Check your Snowflake account profile to make sure that it contains your fist and last name. 

1. Select Data Products \> Partner Connect in the navigation bar on the left hand side of your screen and search for Coalesce in the search bar.   
     
   **![][image1]**
 

2. Review the connection information and then click Connect. ![][image2]

3. When prompted, click Activate to activate your account. You can also activate your account later using the activation link emailed to your address. ![][image3]  
4. Once you’ve activated your account, fill in your information to complete the activation process. ![][image4]

Congratulations\! You’ve successfully created your Coalesce trial account. 

### Step 3: Set Up The Ski Store Dataset

1. We will be using a M Warehouse size within Snowflake for this lab. You can upgrade this within the admin tab of your Snowflake account.

![][image5]

2. In your Snowflake account, click on the Worksheets Tab in the left-hand navigation bar.

![][image6]

3. Within Worksheets, click the "+" button in the top-right corner of Snowsight and choose "SQL Worksheet.”   
   

![][image7]

4. Paste the setup SQL from below into the worksheet that you just created:

```
CREATE or REPLACE schema pc_coalesce_db.calls;

CREATE or REPLACE file format csvformat
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  type = 'CSV';

CREATE or REPLACE stage pc_coalesce_db.calls.call_transcripts_data_stage
  file_format = csvformat
  url = 's3://sfquickstarts/misc/call_transcripts/';

CREATE or REPLACE table pc_coalesce_db.calls.CALL_TRANSCRIPTS ( 
  date_created date,
  language varchar(60),
  country varchar(60),
  product varchar(60),
  category varchar(60),
  damage_type varchar(90),
  transcript varchar
);

COPY into pc_coalesce_db.calls.CALL_TRANSCRIPTS
  from @pc_coalesce_db.calls.call_transcripts_data_stage;

```

### Step 4: Add the Cortex Package from the Coalesce Marketplace

You will need to add the ML Forecast node into your Coalesce workspace in order to complete this lab. 

1. Launch your workspace within your Coalesce account 

 ![][image8]

2. Navigate to the build settings in the lower left hand corner of the left sidebar

![][image9]

3. Select Packages from the Build Settings options  
    

![][image10]

4. Select Browse to Launch the Coalesce Marketplace 

 ![][image11]

5. Select Find out more within the Cortex package

![][image12]

6. Copy the package ID from the Cortex page   
   

![][image13]

7. Back in Coalesce, select the Install button:

![][image14]

8. Paste the Package ID into the corresponding input box:

![][image15]

9. Give the package an Alias, which is the name of the package that will appear within the Build Interface of Coalesce. And finish by clicking Install. 

   

![][image16]

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
## Conclusion And Resources
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What You Learned
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files

### Related Resources
- <link to github code repo>
- <link to documentation>
