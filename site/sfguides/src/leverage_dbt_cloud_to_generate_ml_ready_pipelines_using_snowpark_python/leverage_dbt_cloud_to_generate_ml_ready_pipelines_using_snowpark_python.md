author: hope-wat
id: leverage_dbt_cloud_to_generate_ml_ready_pipelines_using_snowpark_python
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Snowflake Guide Template
<!-- ------------------------ -->
## Overview 
Duration: 3

The focus of this workshop will be to demonstrate how we can use both *SQL and python together* in the same workflow to run *both analytics and machine learning models* on dbt Cloud.

All code in today’s workshop can be found on [GitHub](https://github.com/dbt-labs/python-snowpark-formula1/tree/python-formula1).

### What you'll use during the lab

- A [Snowflake account](https://trial.snowflake.com/) with ACCOUNTADMIN access
- A [dbt Cloud account](https://www.getdbt.com/signup/)
- A [GitHub](https://github.com/) Account 

### What you'll learn

- How to use dbt with Snowflake to build scalable transformations using SQL and Python
    - How to use dbt SQL to prepare your data from sources to encoding 
    - How to train a model in dbt python and use it for future prediction 
    - How to deploy your full project 

### What you need to know

- Basic to intermediate SQL and python.
- Basic understanding of dbt fundamentals. We recommend the [dbt Fundamentals course](https://courses.getdbt.com/collections) if you're interested.
- High level machine learning process (encoding, training, testing)
- Simple ML algorithms &mdash; we will use logistic regression to keep the focus on the *workflow*, not algorithms!

### What you'll build

- A set of data analytics and prediction pipelines using Formula 1 data leveraging dbt and Snowflake, making use of best practices like data quality tests and code promotion between environments
- We will create insights for:
    1. Finding the lap time average and rolling average through the years (is it generally trending up or down)?
    2. Which constructor has the fastest pit stops in 2021?
    3. Predicting the position of each driver based on a decade of data. 

As inputs, we are going to leverage Formula 1 datasets hosted on a dbt Labs public S3 bucket. We will create a Snowflake Stage for our CSV files then use Snowflake’s `COPY INTO` function to copy the data in from our CSV files into tables. The Formula 1 is available on [Kaggle](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020). The data is originally compiled from the [Ergast Developer API](http://ergast.com/mrd/).

## Configure Snowflake
In this section we’re going to sign up for a Snowflake trial account and enable Anaconda-provided Python packages.

1. [Sign up for a Snowflake Trial Account using this form](https://signup.snowflake.com/) if you don’t have one. Ensure that your account is set up using **AWS** in the **US East (N. Virginia)**. We will be copying the data from a public AWS S3 bucket hosted by dbt Labs in the us-east-1 region. By ensuring our Snowflake environment setup matches our bucket region, we avoid any multi-region data copy and retrieval latency issues.

![Puppy](assets/SAMPLE.jpg)

<Lightbox src="/assets/2-configure-snowflake/1-snowflake-trial-AWS-setup.png" title="Snowflake trial"/>

3. After creating your account and verifying it from your sign-up email, Snowflake will direct you back to the UI called Snowsight.

4. When Snowsight first opens, your window should look like the following, with you logged in as the ACCOUNTADMIN with demo worksheets open:

<Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/2-snowflake-configuration/2-new-snowflake-account.png" title="Snowflake trial demo worksheets"/>


5. Navigate to **Admin > Billing & Terms**. Click **Enable > Acknowledge & Continue** to enable Anaconda Python Packages to run in Snowflake.
    
<Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/2-snowflake-configuration/3-accept-anaconda-terms.jpeg" title="Anaconda terms"/>

<Lightbox src="/img/guides/dbt-ecosystem/dbt-python-snowpark/2-snowflake-configuration/4-enable-anaconda.jpeg" title="Enable Anaconda"/>

6. Finally, create a new Worksheet by selecting **+ Worksheet** in the upper right corner.

<!-- ------------------------ -->
## Metadata Configuration
Duration: 2

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:


- **summary**: This is a sample Snowflake Guide 
  - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
- **id**: sample 
  - make sure to match the id here with the name of the file, all one word.
- **categories**: data-science 
  - You can have multiple categories, but the first one listed is used for the icon.
- **environments**: web 
  - `web` is default. If this will be published for a specific event or  conference, include it here.
- **status**: Published
  - (`Draft`, `Published`, `Deprecated`, `Hidden`) to indicate the progress and whether the sfguide is ready to be published. `Hidden` implies the sfguide is for restricted use, should be available only by direct URL, and should not appear on the main landing page.
- **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
- **tags**: Getting Started, Data Science, Twitter 
  - Add relevant  tags to make your sfguide easily found and SEO friendly.
- **authors**: Daniel Myers 
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