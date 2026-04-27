#!/usr/bin/env python3
"""
Prepare AEM payload for content fragment and page updates.

This script replaces the Workato Python code that:
1. Validates tags match snowflake-site:taxonomy format
2. Builds URL-encoded form data for AEM Sling POST requests
3. Generates payloads for both content fragment and page updates
"""

import argparse
import json
import re
import sys
import urllib.parse
from datetime import datetime, timezone

TAG_REGEX = re.compile(r"^snowflake-site:taxonomy(?:/[A-Za-z0-9_-]+)+$")


def validate_tags(tags_csv: str) -> list[str]:
    """
    Validate and parse tags from CSV string.
    Returns sorted unique list of valid tags.
    Raises ValueError for invalid tag formats.
    """
    normalized_csv = (tags_csv or "").strip()
    if normalized_csv.startswith("[") and normalized_csv.endswith("]"):
        normalized_csv = normalized_csv[1:-1].strip()
    
    parsed_tags = [t.strip() for t in normalized_csv.split(",") if t.strip()]
    invalid_tags = [t for t in parsed_tags if not TAG_REGEX.fullmatch(t)]
    
    if invalid_tags:
        raise ValueError(
            f"Invalid tag format(s): {', '.join(invalid_tags)}. "
            "Tags must match 'snowflake-site:taxonomy/<subpath>' with at least "
            "one subfolder and only letters, numbers, underscores, or hyphens per segment."
        )
    
    return sorted(set(parsed_tags))


def build_content_fragment_payload(
    jcr_title: str,
    quickstart_title: str,
    quickstart_slug: str,
    quickstart_body: str,
    quickstart_summary: str,
    quickstart_author: str,
    quickstart_authors: str,
    fork_repo_link: str,
    open_in_snowflake_link: str,
    tags: list[str]
) -> str:
    """
    Build URL-encoded form data for AEM content fragment Sling POST.
    """
    form_data = []
    
    tags_field = "./data/master/quickstartArticleTags"
    form_data.append((f"{tags_field}@TypeHint", "String[]"))
    for tag in tags:
        form_data.append((tags_field, tag))
    
    if jcr_title:
        form_data.append(("./jcr:title", jcr_title))
    if quickstart_title:
        form_data.append(("./data/master/quickstartArticleTitle", quickstart_title))
    if quickstart_slug:
        form_data.append(("./data/master/quickstartArticleSlug", quickstart_slug))
    if fork_repo_link:
        form_data.append(("./data/master/quickstartArticleForkRepoLink", fork_repo_link))
    if open_in_snowflake_link:
        form_data.append(("./data/master/quickstartArticleOpenInSnowflakeLink", open_in_snowflake_link))
    # Use authors if available, otherwise fall back to author
    author_value = quickstart_authors or quickstart_author
    if author_value:
        form_data.append(("./data/master/quickstartArticleAuthor", author_value))
    if quickstart_summary:
        form_data.append(("./data/master/quickstartArticleSummary", quickstart_summary))
    if quickstart_body:
        form_data.append(("./data/master/quickstartArticleBody", quickstart_body))
    
    custom_last_modified = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}T00:00:00.000Z"
    form_data.append(("./jcr:lastModified", custom_last_modified))
    
    return urllib.parse.urlencode(form_data, safe=":/")


def build_page_payload(
    jcr_title: str,
    content_fragment_path: str,
    tags: list[str]
) -> str:
    """
    Build URL-encoded form data for AEM page Sling POST.
    """
    page_form_data = []
    
    page_tags_field = "./jcr:content/cq:tags"
    page_form_data.append((f"{page_tags_field}@TypeHint", "String[]"))
    for tag in tags:
        page_form_data.append((page_tags_field, tag))
    
    if content_fragment_path:
        page_form_data.append(("./jcr:content/quickStartFragmentPath", content_fragment_path))
    if jcr_title:
        page_form_data.append(("./jcr:content/jcr:title", jcr_title))
    
    custom_pub_date = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}T00:00:00.000Z"
    page_form_data.append(("./jcr:content/customPublicationDate", custom_pub_date))
    
    return urllib.parse.urlencode(page_form_data, safe=":/")


def prepare_aem_payload(
    parsed_markdown: dict,
    content_fragment_path: str,
    language: str = "en"
) -> dict:
    """
    Prepare AEM payloads from parsed markdown data.
    
    Args:
        parsed_markdown: Output from parse_markdown.py
        content_fragment_path: Full path to the content fragment in AEM
        language: Language code (default: en)
    
    Returns:
        Dictionary with content_fragment_payload and page_payload
    """
    tags = validate_tags(parsed_markdown.get("categories", ""))
    
    fork_repo_link = parsed_markdown.get("fork_repo_link", "")
    if not fork_repo_link and parsed_markdown.get("id"):
        fork_repo_link = f"https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/{parsed_markdown['id']}"
    
    content_fragment_payload = build_content_fragment_payload(
        jcr_title=parsed_markdown.get("title", ""),
        quickstart_title=parsed_markdown.get("title", ""),
        quickstart_slug=parsed_markdown.get("id", ""),
        quickstart_body=parsed_markdown.get("markdown", ""),
        quickstart_summary=parsed_markdown.get("summary", ""),
        quickstart_author=parsed_markdown.get("author", ""),
        quickstart_authors=parsed_markdown.get("authors", ""),
        fork_repo_link=fork_repo_link,
        open_in_snowflake_link=parsed_markdown.get("open_in_snowflake_link", ""),
        tags=tags
    )
    
    page_payload = build_page_payload(
        jcr_title=parsed_markdown.get("title", ""),
        content_fragment_path=content_fragment_path,
        tags=tags
    )
    
    return {
        "content_fragment_payload": content_fragment_payload,
        "page_payload": page_payload,
        "tags": tags,
        "content_fragment_path": content_fragment_path
    }


def main():
    parser = argparse.ArgumentParser(
        description='Prepare AEM payload from parsed markdown JSON'
    )
    parser.add_argument(
        'input_json',
        help='Path to JSON file from parse_markdown.py or "-" for stdin'
    )
    parser.add_argument(
        '--content-fragment-path',
        required=True,
        help='Full AEM path for the content fragment'
    )
    parser.add_argument(
        '--language',
        default='en',
        help='Language code (default: en)'
    )
    parser.add_argument(
        '--output-json',
        help='Output file path (default: stdout)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.input_json == '-':
            parsed_markdown = json.load(sys.stdin)
        else:
            with open(args.input_json, 'r', encoding='utf-8') as f:
                parsed_markdown = json.load(f)
        
        result = prepare_aem_payload(
            parsed_markdown,
            args.content_fragment_path,
            args.language
        )
        
        output = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output_json:
            with open(args.output_json, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✅ Output written to {args.output_json}", file=sys.stderr)
        else:
            print(output)
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
