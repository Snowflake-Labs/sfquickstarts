#!/usr/bin/env node
/*
  Validate 'title' presence in markdown metadata.
  Accepts front matter (YAML) or loose top-of-file key: value format.

  Inputs via env vars:
    - FILE_LIST_JSON: JSON array of file paths to scan
*/

const fs = require('fs');
const matter = require('gray-matter');

function getFiles() {
  try {
    const raw = process.env.FILE_LIST_JSON || '[]';
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch (e) {
    return [];
  }
}

function extractTitle(content) {
  // Try gray-matter front matter first
  try {
    const fm = matter(content);
    const t = fm?.data?.title;
    if (typeof t === 'string' && t.trim().length > 0) return t.trim();
  } catch {}

  // Fallback: scan first ~120 lines for a 'title:' line
  const head = content.split(/\r?\n/, 120);
  const idx = head.findIndex((l) => /^\s*title\s*:/i.test(l));
  if (idx === -1) return '';
  const value = head[idx].replace(/^\s*title\s*:/i, '').trim();
  return value;
}

const files = getFiles();
const issues = [];

for (const filePath of files) {
  if (!filePath.endsWith('.md')) continue;
  if (!fs.existsSync(filePath)) continue;
  const content = fs.readFileSync(filePath, 'utf8');
  const title = extractTitle(content);
  if (!title || title.length === 0) {
    issues.push({ file: filePath, reason: 'missing or empty title' });
  }
}

if (issues.length) {
  try {
    fs.writeFileSync('title-error.json', JSON.stringify({ issues }, null, 2));
  } catch {}
  console.error('Title validation failed. See title-error.json for details.');
  for (const i of issues) {
    console.error(`- ${i.file}: ${i.reason}`);
  }
  process.exit(1);
} else {
  console.log('Title validation passed.');
}


