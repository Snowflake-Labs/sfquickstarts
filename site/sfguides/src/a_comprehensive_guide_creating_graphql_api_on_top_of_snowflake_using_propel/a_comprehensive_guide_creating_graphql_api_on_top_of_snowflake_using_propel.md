author: YK
id: a_comprehensive_guide_creating_graphql_api_on_top_of_snowflake_using_propel
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# A Comprehensive Guide: Creating GraphQL API on Top of Snowflake Using Propel

## **Introduction**

In this guide, we focus on using [Propel](https://www.propeldata.com/) to create a GraphQL API on top of Snowflake. While there are other methods to interface with Snowflake—such as Snowflake's REST API and language-specific connectors—this guide will concentrate on the Propel method. For a broader understanding of all three methods, refer to the comprehensive guide on Snowflake Medium: [Snowflake API: Comprehensive Guide to 3 Methods With Examples](https://medium.com/snowflake/snowflake-api-comprehensive-guide-to-3-methods-with-examples-c633f4eb35e1).

### **Overview of Using Propel**

Propel offers a seamless way to create fast, efficient GraphQL APIs over your Snowflake data. This method is particularly advantageous for scenarios demanding low latency and high concurrency, such as customer-facing analytics dashboards.

If you prefer a video overview, feel free to take a look at our interview with Snowflake's Daniel Myers on Snowflake's YouTube channel: [Using Propel To Accelerate The Process Of Creating Analytics For Web And Mobile Applications](https://www.youtube.com/watch?v=AO87CZOK7Ko).

### **Prerequisites**

- Basic understanding of Snowflake and GraphQL
- Access to Snowflake instance
- [A Propel account](https://console.propeldata.com/get-started/)

### **What You’ll Learn**

- Setting up data in Snowflake for Propel integration
- Configuring Propel to work with Snowflake
- Creating and testing GraphQL APIs on top of your Snowflake data

### **What You’ll Build**

- A low-latency, high-concurrency GraphQL API on top of Snowflake using Propel

Let's proceed.


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