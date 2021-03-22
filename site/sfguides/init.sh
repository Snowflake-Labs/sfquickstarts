#!/bin/bash
#
# init.sh
#
# Automate these steps to get yourself up and running with SFGuide:
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
	echo "USAGE: $0 <SFGUIDE_NAME>"
	echo ""
	exit 1
fi

# env variables
SFGUIDE_NAME=$1
AUTHOR_NAME=`git config user.name`

# local variables
sfguide_markdown_filename="markdown/$SFGUIDE_NAME/$SFGUIDE_NAME.md"
sfguide_package_json_filename="markdown/$SFGUIDE_NAME/package.json"
markdown_template="markdown/_template/markdown.template"
package_json_template="markdown/_template/package.json"
#in MacOS sed creates a backup file if zero length extension is not specified e.g. ''
backup_md="$sfguide_markdown_filename-e"
backup_package_json="markdown/$SFGUIDE_NAME/package.json-e"

# validate that markdown template and package.json exist
if [ ! -f "$markdown_template" ] || [ ! -f "$package_json_template" ]; then
  msg "ERROR!"
  echo "Could not find one of the following files:"
  echo "  - $markdown_template"
  echo "  - $package_json_template"
  echo ""
  exit 0
fi

# Create a new directory for the sfguide 
mkdir markdown/$SFGUIDE_NAME
cp -r markdown/_template/* markdown/$SFGUIDE_NAME/

# rename markdown template file 
mv markdown/$SFGUIDE_NAME/markdown.template $sfguide_markdown_filename

# replace placeholder sfguide id in markdown template file with name provided by command line argument 
sed -i \
  -e "s/SFGUIDE_NAME.*/$SFGUIDE_NAME/g" \
  $sfguide_markdown_filename

# replace placeholder authorname with git username=
sed -i \
  -e "s/AUTHOR_NAME.*/$AUTHOR_NAME/g" \
  $sfguide_markdown_filename

# replace placeholder sfguide name in the watch command with name provided in command line argument
sed -i \
  -e "s/SFGUIDE_NAME/$SFGUIDE_NAME/g" \
  $sfguide_package_json_filename

if [ -f "$backup_md" ]; then
  rm $backup_md
fi

if [ -f "$backup_package_json" ]; then
  rm $backup_package_json
fi

echo "Markdown file created! Find it at $PWD/markdown/$SFGUIDE_NAME"

command_exists claat
command_exists go