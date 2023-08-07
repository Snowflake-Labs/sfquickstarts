# Snowflake Quickstarts

[![Demo](https://drive.google.com/uc?export=view&id=1wPgQExjdIONOtYruMKyeknvMvTDlVJEY)](https://drive.google.com/uc?export=view&id=1Dg3s5-KK-TzFZti63XButyDaTzcuZFxE)

## What are Snowflake Quickstarts?
Snowflake Quickstarts are interactive tutorials and self-serve demos written in markdown syntax. Quickstarts provide a unique step-by-step reading experience and automatically saves tutorial progress for readers. These tutorials are published at [quickstarts.snowflake.com](https://guides.snowflake.com/)

You can submit your own Quickstarts to be published on Snowflake's website by submitting a pull request to this repo. This repository contains all the tools and documentation you’ll need for building, writing, and submitting your own Quickstart!


## What's special about the Quickstart format?

* Powerful and flexible authoring flow in Markdown text
* Ability to produce interactive web or markdown tutorials without writing any code
* Easy interactive previewing
* Usage monitoring via Google Analytics
* Support for multiple target environments or events (conferences, kiosk, web, offline, etc.)
* Support for anonymous use - ideal for public computers at developer events
* Looks great, with a responsive web implementation
* Remembers where the student left off when returning to a quickstarts
* Mobile friendly user experience

## Getting Started

### Prerequisites

  1. [Install Node Version Manager (nvm)](https://github.com/nvm-sh/nvm#installing-and-updating)
     - Not sure if you have it installed? Run `nvm` or `nvm -v` at the command line and hit enter. If you encounter a "command not found" error, you likely do not have it installed.
  2. Install Node v14 (required to run the site locally) using nvm: `nvm install 14`
     - If you have Homebrew installed, run: `brew install node@14`
  3. Install gulp-cli `npm i -g gulp-cli`
  4. [Install Go](https://golang.org/doc/install)
     - If you have Homebrew installed, run: `brew install golang`
     - Install claat `go install github.com/googlecodelabs/tools/claat@latest`
     - Ensure go and claat is in your `PATH` [claat path setup](#claat-related-errors)
  5. **Optional**: install the live-reload plugin for Chrome: [LiveReload](https://chrome.google.com/webstore/detail/livereload/jnihajbhpnppcggbcgedagnkighmdlei)

### Run locally

  1. Fork this repository to your personal GitHub account (top right of webpage, `fork` button)
  2. Clone your new fork `git clone git@github.com:<YOUR-USERNAME>/sfquickstarts.git sfquickstarts`
  3. Navigate to the site directory `cd sfquickstarts/site`
  4. Set the project to use Node v14 by running `nvm use`. If you an encounter an error stating you don't have the correct version installed, run `nvm install`. For more help, see steps 1 and 2 in the Prerequisites above.
  5. Install node dependencies `npm install`
  6. Run the site `npm run serve`
  7. Open a browser to http://localhost:8000/

Congratulations! You now have the Snowflake Quickstarts landing page running.

### Common Errors

#### 1. Claat related errors
   - Make sure Go is properly in your `PATH`. Add the following lines to your profile (`~/.profile`, or `~/.zshrc`):
````bash
#adding Golang to path
export PATH=$PATH:/usr/local/go/bin
export PATH=$PATH:$HOME/go/bin
````
  ***Note:** After adding Go to your `PATH`, be sure to apply your new profile: `source ~/.profile` or `source ~/.zshrc`*

#### 2. You get a `EACCES` error when installing `gulp-cli`
   - This means that your npm location needs to be updated. Follow the steps here: [Resolve EACCESS permissions](https://docs.npmjs.com/resolving-eacces-permissions-errors-when-installing-packages-globally#manually-change-npms-default-directory)

#### 3. You get `Error: Cannot find module 'postcss'` when running `npm run serve` 
   - The module may not have been installed for some reason so run `npm install --save-dev postcss gulp-postcss` and then rerun `npm run serve` 

## Write Your First Quickstart

  1. Terminate the running server with `ctrl C` and navigate to the `sfguides` source directory `cd sfguides/src`
     - In this directory, you will see all existing guides and their markdown files.
  2. Generate a new guide from the guide template `npm run template <GUIDE_NAME>` 
      - Don't use spaces in the name of your guide, instead use hyphens.
  3. Navigate to the newly generated guide (`cd sfguides/src/<GUIDE-NAME>`) and edit your guide in a tool like VS Code.
  4. Run the website again `npm run serve`
  5. As you edit and save changes, your changes will automatically load in the browser.

You can always read the [sample Quickstart](site/sfguides/src/sample/sample.md) online.

### Tips

- Review the [sample.md](site/sfguides/src/sample/sample.md) file to learn more about how to structure your Quickstart for the claat tool. 
- You can see the supported Quickstart categories [here](site/app/styles/_overrides.scss). If you want to suggest a new category please create a GitHub issue!
- Checkout [how to use VS Code to write markdown files](https://code.visualstudio.com/docs/languages/markdown)
- If you want to learn more about Quickstarts, check out this [excellent tutorial](https://medium.com/@zarinlo/publish-technical-tutorials-in-google-codelab-format-b07ef76972cd)

## How do I get my Snowflake Quickstart on [quickstarts.snowflake.com](https://quickstarts.snowflake.com)?

1. You will need to sign Snowflake's CLA 
2. Fork this repository
3. Clone it to your local system
4. Make a new branch
5. Make your changes
6. Push it back to your repo
7. Open this repository on GitHub.com
8. Click the Pull Request button to open a new pull request
9. Snowflake will review and approve the submission

To learn more about how to submit a pull request on GitHub in general, check out GitHub's [official documentation](https://docs.github.com/en/free-pro-team@latest/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork).

## Reporting issues or errata in Quickstarts

Quickstarts are not in the scope of Snowflake Global Support. Please do not file support cases for issues or errata in a Quickstart. If you encounter an issue in a Quickstart (outdated copy or data, typos, broken links, etc.), [please file an issue](https://github.com/Snowflake-Labs/sfquickstarts/issues/new/choose) in this repository. Be sure to include the following information:

1. The title of the Quickstart
2. A link to the Quickstart
3. A description of the problem
4. A proposed solution, if applicable (optional)
