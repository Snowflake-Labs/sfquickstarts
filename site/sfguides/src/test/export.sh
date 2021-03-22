#!/bin/bash
#
# export.sh
#
# export the sfguide to the right directory

# Get markdown file name
sfguide_markdown_filename=`ls *.md`
rm -fr temp

claat export -ga UA-41491190-9 -o ../../dist/ $sfguide_markdown_filename
