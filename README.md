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

  1. A GitHub account
  2. A code editor (e.g. VS Code) 


### How to:

**Create a new Guide Locally:**
  1. Fork this repository to your personal GitHub account (top right of webpage, `fork` button)
  2. Clone your new fork `git clone git@github.com:<YOUR-USERNAME>/sfquickstarts.git sfquickstarts`
  3. Navigate to the directory `cd sfquickstarts/site/src`
  4. Create a new branch `git checkout -b <your-branch-name>` (make sure you are working on a new branch and not on `master`!) 
  6. Copy the template folder and rename it appropriately: (e.g. `cp _template my-quickstart-name-here` in your terminal). 
  7. Start authoring in markdown format.  Note this [Markdown Template](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/_template/markdown.template).
  8. Make sure you select the appropriate language and category tags from [the list in this Guide](https://www.snowflake.com/en/developers/guides/get-started-with-guides/). You will not be able to merge your changes without this step!


**Submit an edit on GitHub.com**
1. Fork this repository to your personal GitHub account (top right of webpage, `fork` button)
2. In your fork, Navigate to the directory `cd sfquickstarts/site/src`
3. Click edit (pencil icon on top right) and make your edits
4. Commit changes - this will create a new branch
5. Create a pull request and submit to Devrel!

```diff
! Congratulations! 
You now have the setup to work on your Snowflake Guide.
```

### Submitting: 
   1. If you need to synchronize your branch with your repo: `git push --set-upstream origin <your-branch-name>`
   2. Create a  **draft PR** pull request against sfquickstarts/master from your fork, using <your-branch-name>.
   3. GitHub will run validation for basic formatting, required fields, tags, and language. If there are errors, you will be notified to correct them. A staging link will be generated for you -- use this to verify that your guide looks as expected! 
   4. Once validation passes, request review from @kanwalzs. Note that the devrel team has a 24 hour SLA for approving PRs. You do not need to post in #devrel to notify us :) 
   5. The devrel team will make sure your branch is up to date with master, and then merge it in. 
   6. Expect content to appear/update on snowflake.com/en/developers/guides within 30 minutes of your PR being merged in. 


### Important Notes 

- Ensure your folder uses "Hyphens (-)" and not "Underscores(_)" in folder name
- Please ensure you include all required pieces in the header.<br>
  - Required items includes: language, category tags, id, author name.<br>
  - Optional items include: Summary, Github Issues link etc.  
- Complete the Get Started with Guides to learn more about about the specifics.  It will give you details on formatting and layout etc.
- Always check if the first step is labeled **Overview** AND then make sure there are these specific sections under that step: <br>1) Overview, <br>2) What You Will Build, <br> 3) What You Will Learn, <br>4) Prerequisite
- Always check if the last step is labeled **Conclusion and Resources** and then make sure it includes these specific sections <br>1) Conclusion, <br>2) What You Learned, and <br>3) Resources (*with links to docs, blogs, videos, etc.*)

> NOTE: If you see any issues or any inconsistencies as outlined above, you may not be able to submit the PR before you resolve those items.

Here are two QS Guides you can take a look as references:

* **Logged Out experience with one click into product:** [Understanding Customer Reviews using Snowflake Cortex](https://www.snowflake.com/en/developers/guides/understanding-customer-reviews-using-snowflake-cortex/)
* **Topic pages with multiple use cases below the Overview:** [Data Connectivity with Snowflake Openflow](https://www.snowflake.com/en/developers/guides/data-connectivity-with-snowflake-openflow/)
* **Simple Hands-on Guide:** [Getting Started with Snowflake Intelligence](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-intelligence/)

Thank you for helping us maintain a high quality bar and consistency across all Snowflake Developer Guides!

## Reporting issues in Guides

Guides are not in the scope of Snowflake Global Support. Please do not file support cases for issues or errata in a Guide. 

However, pull requests are welcome! If you encounter an issue in a Guide (outdated copy or data, typos, broken links, etc.), please submit a pull request and contribute to keeping our Guides up to date and awesome. 
