# Snowflake Guides


## What are Snowflake Guides?
Snowflake Guides serves as a collection of what previously were "Snowflake Quickstarts" and "Snowflake Solutions Center" along with some new additional types of content.  

Guides are interactive tutorials and self-serve demos written in markdown syntax. Guides provide a unique step-by-step reading experience and automatically saves tutorial progress for readers. These tutorials are published at: [https://www.snowflake.com/en/developers/guides/](https://www.snowflake.com/en/developers/guides/)

You can submit your own Guides to be published on Snowflake's website by submitting a pull request to this repo. This repository contains all the tools and documentation you’ll need for building, writing, and submitting your own Guide


## What's special about the Snowflake Guides?

* Powerful and flexible authoring flow in Markdown text
* Ability to produce interactive web or markdown tutorials without writing any code
* Easy interactive previewing (using GitHub or Visual Studio Code preview feature)
* Support for anonymous use - ideal for public computers at developer events
* Looks great, with web implementation on snowflake.com
* Anchors to content to make it easy to scroll on a single page

## Getting Started

### Prerequisites

  1. Have VS Code Installed
  2. Have a GitHub account
  3. [Request a Repository](https://docs.google.com/forms/d/1AQ0SOMi0-kAHHluEx9HJDDUctwisHqrSVWo-wvfDMwU/edit#responses) to be created on GitHub.
  


### Setup:

  1. Fork this repository to your personal GitHub account (top right of webpage, `fork` button)
  2. Clone your new fork `git clone git@github.com:<YOUR-USERNAME>/sfquickstarts.git sfquickstarts`
  3. Navigate to the site directory `cd sfquickstarts/site`
  4. Navigate to your Guide folder
  5.  Start authoring in markdown format.  Feel free to use this [Markdown Template](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/_template/markdown.template).

```diff
! Congratulations! 
You now have the setup to work on your Snowflake Guide.
```



### Common Errors

- Ensure your folder uses "Hyphens (-)" and not "Underscores(_)" in folder name
- Please ensure you include all required pieces in the header.<br>
   Required items includes: language, category tags, id, author name.<br>
   Optional items include: Summary, Github Issues link etc.  
- Complete the Get Started with Guides to learn more about about the specifics.  It will give you details on formatting and layout etc.




## Write Your First Guide

  
  ### Formatting your Guide:
   - Always check if the first step is labeled **Overview** AND then make sure there are these specific sections under that step: <br>**1) Overview, <br>2) What You Will Build, <br> 3) What You Will Learn, <br>4) Prerequisites**<p>
   - Always check if the last step is labeled **Conclusion and Resources** and then make sure it includes these specific sections <br>1) Conclusion, <br>2) What You Learned, and <br>3) Resources (*with links to docs, blogs, videos, etc.*)<p>
   - Once you complete authoring your Guide, create a PR to submit.  
   - Prior to submitting, the Guide will go through some basic checks for formatting, required fields, tags, and language.
   - If there are errors, you will be notified to correct them
   - Once errors are corrected, submit the PR
   

> NOTE: If you see any issues or any inconsistencies as outlined above, you will not be able to submit the PR before you resolve those items.

Here are three QS Guides you can take a look as references:

* **Logged Out experience with one click into product:** [Understanding Customer Reviews using Snowflake Cortex](https://www.snowflake.com/en/developers/guides/understanding-customer-reviews-using-snowflake-cortex/)
* **Topic pages with multiple use cases below the Overview:** [Data Connectivity with Snowflake Openflow](https://www.snowflake.com/en/developers/guides/data-connectivity-with-snowflake-openflow/)


We want to maintain a standard and consistency across all QS guides and it's very imp that we all follow these guidelines. Really appreciate your help and support. 

## Checks at PR submission.

- Once you submit your PR, it comes to DevRel for approval.  
- A staging link is generated for your preview.  Please remember, this is not live yet and your final URL WILL BE different.
- When the PR is reviewed and merged, your Guide is live and visible on [www.snowflake.com/en/developers/guides](ttps://www.snowflake.com/en/developers/guides).


#### Important Tips

- List of complete categories is outlined in Get Started with Guides.  Please review carefully
- All language tags that can be used are also covered in the Guide.  This ensures the content is visible in the regions.  Please apply the correct language tag.





## Reporting issues in Guides

Guides are not in the scope of Snowflake Global Support. Please do not file support cases for issues or errata in a Guide. <p>If you encounter an issue in a Guide (outdated copy or data, typos, broken links, etc.), please create an issue and tag the author!  Author names are displayed on the page.

Be sure to include the following information:

1. Title of the Guide
2. Link to the specific page/step of Guide
3. A description of the problem
4. A proposed solution, if applicable (optional)
