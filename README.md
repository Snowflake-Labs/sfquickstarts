# Snowflake Devlabs

[![Demo](https://storage.googleapis.com/claat/demo.png)](https://storage.googleapis.com/claat/demo.mp4)

## What are Devlabs?
Devlabs are interactive tutorials and self-serve demos written in markdown syntax. Devlabs provide a unique step-by-step reading experience and automatically saves tutorial progress for readers. These tutorials are published at [developers.snowflake.com/devlabs](developers.snowflake.com/devlabs)

You can submit your own devlab to be published on Snowflake's website by submitting a pull request to this repo. This repository contains all the tools and documentation you’ll need for building, writing, and submitting your own devlabs!


## What's special about the Devlab format?

* Powerful and flexible authoring flow in Markdown text
* Ability to produce interactive web or markdown tutorials without writing any code
* Easy interactive previewing
* Usage monitoring via Google Analytics
* Support for multiple target environments or events (conferences, kiosk, web, offline, etc.)
* Support for anonymous use - ideal for public computers at developer events
* Looks great, with a responsive web implementation
* Remembers where the student left off when returning to a codelab
* Mobile friendly user experience

## How to get started

  1. nodejs & npm ([Install NodeJS & npm](https://nodejs.org/en/download/))
  2. install gulp-cli:
   ````bash
   npm install --global gulp-cli
   ````
  3. install Golang ([Install Go](https://golang.org/doc/install))
  4. add `/usr/local/go/bin` to the `PATH` environment variable. You can do this by adding the following line to your profile (`.bashrc` or `.zshrc`):

````bash
export PATH=$PATH:/usr/local/go/bin
````
***Note: Changes made to a profile file may not apply until the next time you log into your computer. To apply the changes immediately, just run the shell commands directly or execute them from the profile using a command such as `source $HOME/.zshrc`.***

  5. install claat:
   ````bash
   go get github.com/googlecodelabs/tools/claat
   ````
  6. navigate to the site directory:
   ````bash
   cd site/
   ````
  7. install dependencies:
   ````bash
   npm install
   ````
  8. run the site locally
   ````bash
   gulp serve
   ````

Congratulations! You now have the DevLabs landing page running.

#### Now lets add our first devlab:

  1. Terminate the running gulp server with `ctrl C` and navigate to the devlab directory
  ````bash
  cd site/devlabs
  ````
  The devlabs directory is where to store all devlab content, written in markdown.
  
  2. Use the claat tool to convert the markdown file to HTML
  ````bash
  claat export sample.md
  ````

  You should see `ok sample` as the response. This means claat has successfully converted your .md file to HTML and created a new directory named `sample`.
   
  3. Now lets run our server again, this time specifying our devlabs directory of content
   ````bash
   gulp serve --codelabs-dir=devlabs
   ````
You can now navigate to the landing page in your browser to see your new codelab!

You can use the [sample devlab](site/devlabs/sample.md) as a template, just change the name of the file and the id listed in the header. 

### Tips

- Review the [sample.md](site/devlabs/sample.md) file to learn more about to to structure your devlab for the claat tool. 
- You can also see more formating information in the [claat documentation](claat/README.md), and use the command `claat -h`
- You can see the supported devlab categories [here](site/app/styles/_overrides.scss). If you want to suggest a new category please create a github issue!

If you want to learn more about devlabs, check out this [excellent tutorial](https://medium.com/@zarinlo/publish-technical-tutorials-in-google-codelab-format-b07ef76972cd)

## How do I publish my Devlab to developers.snowflake.com?

1. You will need to sign Snowflake's CLA 
2. Fork this repository
3. Clone it to your local system
4. Make a new branch
5. Make your changes
6. Push it back to your repo
7. Open this repository on GitHub.com
8. Click the Pull Request button to open a new pull request
9. Snowflake will review and approve the submission

To learn more how to submit a pull request on GitHub in general, checkout github's [official documentation](https://docs.github.com/en/free-pro-team@latest/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork).
