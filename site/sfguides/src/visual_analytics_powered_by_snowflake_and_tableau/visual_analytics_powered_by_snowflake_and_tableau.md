author: Chandra Nayak & Bailey Ferrari
id: visual_analytics_powered_by_snowflake_and_tableau
summary: Visual Analytics Powered by Snowflake and Tableau
categories: Getting Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Visual Analytics powered by Snowflake and Tableau
<!-- ------------------------ -->
## Overview 
Duration: 90

Join Snowflake and Tableau for an instructor-led hands-on lab to learn how to build governed, visual, and interactive analytics quickly and easily. 


The rest of this Snowflake Guide explains the steps of writing your own guide. 

### Prerequisites
- Familiarity with Snowflake and Tableau

### What You’ll Learn 
- Load unstructured data from IoT enabled bikes into Snowflake.
- Integrate and deliver multi-tenant tables and views in Snowflake to Tableau for real-time dashboarding.
- Use API integration to load geospatial data into Snowflake. 
- Securely connect to your Snowflake data by leveraging Virtual Connections and Centralized Row Level Security in Tableau.
- Build visual, intuitive, and interactive data visualizations powered by live data in Snowflake.
- Share production-ready Tableau dashboards by embedding the visualizations into your custom application.
- Showcase your data in the Snowflake Data Marketplace.


### What You’ll Need 
- A [Snowflake](https://trial.snowflake.com/) Account 
- A [Tabelau Online](https://www.tableau.com/products/online/request-trial) Account


### What You’ll Build 
- A Snowflake Guide

<!-- ------------------------ -->
## Metadata Configuration
Duration: 2

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:


- **summary**: This is a sample Snowflake Guide 
  - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
- **id**: visual_analytics_powered_by_snowflake_and_tableau
  - make sure to match the id here with the name of the file, all one word.
- **categories**: data-engineering 
  - You can have multiple categories, but the first one listed is used for the icon.
- **environments**: web 
  - `web` is default. If this will be published for a specific event or  conference, include it here.
- **status**: Published
  - (`Draft`, `Published`, `Deprecated`, `Hidden`) to indicate the progress and whether the sfguide is ready to be published. `Hidden` implies the sfguide is for restricted use, should be available only by direct URL, and should not appear on the main landing page.
- **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
- **tags**: Getting Started, Data Engineering, Twitter 
  - Add relevant  tags to make your sfguide easily found and SEO friendly.
- **authors**: Chandra Nayak , Bailey Ferrari 
  - Indicate the author(s) of this specific sfguide.

---

You can see the source metadata for this guide you are reading now, on [the github repo](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md).


<!-- ------------------------ -->
## Snowflake Configuration
Duration: 2
1. Login to your Snowflake Trial account

2. We will be using the new UI to getting started but you can also switch over to the Classic Console if you would like. 

Classic UI: 
If you ever want to change from the new UI to the classic one, click on the home button and then Classic Console 
```markdown
## Step 1 Title
Duration: 3

Connect to your Snowflake Account.

## Step 2 Title
Duration: 1

All the content for the step goes here.
```

To indicate how long each step will take, set the `Duration` under the step title (i.e. `##`) to an integer. The integers refer to minutes. If you set `Duration: 4` then a particular step will take 4 minutes to complete. 

The total sfguide completion time is calculated automatically for you and will be displayed on the landing page. 

<!-- ------------------------ -->

<!-- ------------------------ -->
## Tableau Configuration
Duration: 2
1. Login to your Snowflake Trial account
A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Tableau Trial Account
Duration: 3

Connect to your Tableau Online Trial Account.

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
Positive
: This will appear in a positive info box.


Negative
: This will appear in a negative info box.

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
![Snowflake Login](assets/new_snowflake_ui.png)

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