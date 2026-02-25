#!/usr/bin/env python3
"""
Parse quickstart markdown files and extract frontmatter + transform content for AEM.

This script replaces the Workato Python code that:
1. Extracts YAML frontmatter (id, title, summary, categories, tags, etc.)
2. Transforms relative image URLs to absolute GitHub raw URLs
3. Outputs JSON for AEM content fragment updates
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def extract_frontmatter(markdown_text: str) -> tuple[dict, str]:
    """
    Extract YAML frontmatter from markdown.
    Returns (frontmatter_dict, content_without_frontmatter)
    """
    text = markdown_text.lstrip("\ufeff")
    
    fm_match = re.match(r'^\s*---\s*\n(.*?)\n---\s*(\n|$)', text, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        content = text[fm_match.end():]
    else:
        sep = re.search(r'\n\s*\n', text)
        if not sep:
            raise ValueError("YAML frontmatter not found at top of markdown.")
        fm_text = text[:sep.start()].strip()
        content = text[sep.end():]
    
    frontmatter = {}
    if yaml:
        try:
            frontmatter = yaml.safe_load(fm_text) or {}
        except Exception:
            frontmatter = parse_frontmatter_manually(fm_text)
    else:
        frontmatter = parse_frontmatter_manually(fm_text)
    
    return frontmatter, content


def parse_frontmatter_manually(fm_text: str) -> dict:
    """Fallback manual YAML parsing for simple key: value pairs."""
    result = {}
    current_key = None
    current_value = []
    
    for line in fm_text.split('\n'):
        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            if current_key:
                result[current_key] = '\n'.join(current_value).strip()
            
            key, _, value = line.partition(':')
            current_key = key.strip()
            current_value = [value.strip()]
        elif current_key:
            current_value.append(line)
    
    if current_key:
        result[current_key] = '\n'.join(current_value).strip()
    
    return result


def transform_image_urls(markdown: str, base_url: str, quickstart_name: str) -> tuple[str, int]:
    """
    Transform relative image URLs to absolute GitHub raw URLs.
    Returns (transformed_markdown, count_of_replacements)
    """
    count = 0
    
    def replace_image(match):
        nonlocal count
        alt_text = match.group(1)
        url = match.group(2)
        
        if url.startswith(('http://', 'https://', '//')):
            return match.group(0)
        
        url = url.lstrip('./')
        
        if url.startswith('assets/'):
            new_url = f"{base_url}/{quickstart_name}/{url}"
        else:
            new_url = f"{base_url}/{quickstart_name}/assets/{url}"
        
        count += 1
        return f"![{alt_text}]({new_url})"
    
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    transformed = re.sub(pattern, replace_image, markdown)
    
    return transformed, count


def normalize_categories(categories) -> str:
    """Normalize categories to AEM tag format."""
    if not categories:
        return ""
    
    if isinstance(categories, list):
        tags = []
        for cat in categories:
            if isinstance(cat, str):
                tag = cat.strip().lower().replace(' ', '-')
                if not tag.startswith('snowflake-site:taxonomy/'):
                    tag = f"snowflake-site:taxonomy/guide-category/{tag}"
                tags.append(tag)
        return ','.join(tags)
    
    if isinstance(categories, str):
        categories_str = categories.strip()
        if categories_str.startswith('[') and categories_str.endswith(']'):
            categories_str = categories_str[1:-1]
        
        tags = []
        for cat in categories_str.split(','):
            tag = cat.strip().strip('"\'').lower().replace(' ', '-')
            if tag:
                if not tag.startswith('snowflake-site:taxonomy/'):
                    tag = f"snowflake-site:taxonomy/guide-category/{tag}"
                tags.append(tag)
        return ','.join(tags)
    
    return ""


def parse_markdown(
    file_path: str,
    commit_sha: str,
    quickstart_name: str,
    base_image_url: str
) -> dict:
    """
    Parse markdown file and return structured data for AEM.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    frontmatter, content = extract_frontmatter(markdown_text)
    
    # Strip H1 header from content since title is displayed in hero section
    content_without_h1 = re.sub(r'^#\s+.+\n*', '', content, count=1)
    
    transformed_content, images_count = transform_image_urls(
        content_without_h1, base_image_url, quickstart_name
    )
    
    qid = frontmatter.get('id', quickstart_name)
    title = frontmatter.get('title', '')
    
    if not title:
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
    
    if not title:
        title = qid
    summary = frontmatter.get('summary', frontmatter.get('description', ''))
    language = frontmatter.get('language', 'en').lower()
    status = frontmatter.get('status', 'Published')
    categories = normalize_categories(frontmatter.get('categories'))
    level = frontmatter.get('level', frontmatter.get('difficulty', ''))
    partner = frontmatter.get('partner', '')
    author = frontmatter.get('author', '')
    authors = frontmatter.get('authors', author)
    if isinstance(authors, list):
        authors = ', '.join(authors)
    
    feedback_link = frontmatter.get('feedback_link', '')
    fork_repo_link = frontmatter.get('fork_repo_link', '')
    if not fork_repo_link:
        fork_repo_link = f"https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/{qid}"
    
    open_in_snowflake_link = frontmatter.get('open_in_snowflake_link', '')
    
    tags = frontmatter.get('tags', [])
    if isinstance(tags, list):
        tags = ', '.join(str(t) for t in tags)
    elif not isinstance(tags, str):
        tags = str(tags) if tags else ''
    
    environments = frontmatter.get('environments', [])
    if isinstance(environments, list):
        environments = ', '.join(str(e) for e in environments)
    elif not isinstance(environments, str):
        environments = str(environments) if environments else ''
    
    duration = frontmatter.get('duration', '')
    if isinstance(duration, int):
        duration = f"{duration} minutes"
    
    legacy_urls = frontmatter.get('legacy_urls', [])
    if isinstance(legacy_urls, str):
        legacy_urls = [u.strip() for u in legacy_urls.split(',') if u.strip()]
    
    return {
        'id': qid,
        'title': title,
        'summary': summary,
        'language': language,
        'status': status,
        'categories': categories,
        'level': level,
        'partner': partner,
        'author': author,
        'authors': authors,
        'tags': tags,
        'environments': environments,
        'duration': duration,
        'feedback_link': feedback_link,
        'fork_repo_link': fork_repo_link,
        'open_in_snowflake_link': open_in_snowflake_link,
        'legacy_urls': [{'url': u} for u in legacy_urls],
        'markdown': transformed_content,
        'images_replaced_count': images_count,
        'commit_sha': commit_sha,
        'quickstart_name': quickstart_name
    }


def main():
    parser = argparse.ArgumentParser(
        description='Parse quickstart markdown and output JSON for AEM'
    )
    parser.add_argument('file_path', help='Path to the markdown file')
    parser.add_argument('--commit-sha', required=True, help='Git commit SHA')
    parser.add_argument('--quickstart-name', required=True, help='Quickstart folder name')
    parser.add_argument(
        '--base-image-url',
        default='https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/site/sfguides/src',
        help='Base URL for image references'
    )
    parser.add_argument('--output-json', help='Output file path (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        result = parse_markdown(
            args.file_path,
            args.commit_sha,
            args.quickstart_name,
            args.base_image_url
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
