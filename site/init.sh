#!/bin/bash
#
# init.sh
#
# Automate these steps to get yourself up and running with SFGuides:
# * Create boilerplate for SFGuide
# * Configure a nodemon watch command to rebuild your sfguide on save
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + -

command_exists() {
    # check if command exists and fail otherwise
    command -v "$1" >/dev/null 2>&1
    if [[ $? -ne 0 ]]; then
        echo "Note: $1 Does not exist. Please install it first!"
    fi
}

cd `dirname $0`

# validate that a sfguide name was included as an argument
if [ "$#" -ne 1 ]; then
	echo "USAGE: npm run template <SFGUIDE_NAME>"
	echo ""
	exit 1
fi

# env variables
SFGUIDE_NAME=`echo $1 | tr '[:upper:]' '[:lower:]' | tr ' ' '_'`
AUTHOR_NAME=`git config user.name`

# local variables
sfguide_markdown_filename="sfguides/src/$SFGUIDE_NAME/$SFGUIDE_NAME.md"
markdown_template="sfguides/src/_template/markdown.template"
#in MacOS sed creates a backup file if zero length extension is not specified e.g. ''
backup_md="$sfguide_markdown_filename-e"

# validate that markdown template exist
if [ ! -f "$markdown_template" ]; then
  msg "ERROR!"
  echo "Could not find one of the following files:"
  echo "  - $markdown_template"
  echo ""
  exit 0
fi

# Create a new directory for the sfguide 
mkdir sfguides/src/$SFGUIDE_NAME
cp -r sfguides/src/_template/* sfguides/src/$SFGUIDE_NAME/

# rename markdown template file 
mv sfguides/src/$SFGUIDE_NAME/markdown.template $sfguide_markdown_filename

# replace placeholder sfguide id in markdown template file with name provided by command line argument 
sed -i \
  -e "s/SFGUIDE_NAME.*/$SFGUIDE_NAME/g" \
  $sfguide_markdown_filename

# replace placeholder authorname with git username=
sed -i \
  -e "s/AUTHOR_NAME.*/$AUTHOR_NAME/g" \
  $sfguide_markdown_filename

# replace placeholder sfguide name in the watch command with name provided in command line argument
if [ -f "$backup_md" ]; then
  rm $backup_md
fi

echo "Markdown file created! Find it at $PWD/sfguides/src/$SFGUIDE_NAME"

command_exists claat
command_exists go