#!/usr/bin/env node
/*
  Validate 'tags' in markdown front matter. Accepts tags in either array form
  or comma-separated string. Each tag must match:
    ^snowflake-site:taxonomy/[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*$

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

function toTagArray(tagsField) {
  if (!tagsField) return [];
  if (Array.isArray(tagsField)) return tagsField.map(String);
  const s = String(tagsField);
  // split on commas, handle optional spaces
  return s.split(/[\,\n]/).map((t) => t.trim()).filter(Boolean);
}

function extractTags(content) {
  // Try gray-matter front matter first
  try {
    const fm = matter(content);
    const fmTags = toTagArray(fm?.data?.tags);
    if (fmTags.length) return fmTags;
  } catch {}

  // Fallback: scan first ~120 lines for a 'tags:' field in loose key:value style
  const head = content.split(/\r?\n/, 120);
  const idx = head.findIndex((l) => /^\s*tags\s*:/i.test(l));
  if (idx === -1) return [];

  const line = head[idx];
  const afterColon = line.replace(/^\s*tags\s*:/i, '').trim();
  if (afterColon) {
    return afterColon.split(',').map((t) => t.trim()).filter(Boolean);
  }

  // YAML list under tags:
  const tags = [];
  for (let i = idx + 1; i < head.length; i++) {
    const l = head[i];
    if (/^\s*-\s+/.test(l)) {
      tags.push(l.replace(/^\s*-\s+/, '').trim());
      continue;
    }
    if (tags.length && (/^\s*$/.test(l) || /^\s*\w[\w\- ]*\s*:\s*.*$/.test(l))) break;
  }
  return tags.filter(Boolean);
}

const TAG_PATTERN = /^snowflake-site:taxonomy\/[a-z0-9][a-z0-9-]*(?:\/[a-z0-9][a-z0-9-]*)*$/;

const files = getFiles();
const issues = [];

for (const filePath of files) {
  if (!filePath.endsWith('.md')) continue;
  if (!fs.existsSync(filePath)) continue;
  const content = fs.readFileSync(filePath, 'utf8');
  const tags = extractTags(content);
  if (!tags.length) continue; // no tags provided is not an error in this check
  const invalid = tags.filter((t) => !TAG_PATTERN.test(String(t).trim().toLowerCase()));
  if (invalid.length) {
    issues.push({ file: filePath, invalid });
  }
}

if (issues.length) {
  try {
    fs.writeFileSync('tags-error.json', JSON.stringify({ issues }, null, 2));
  } catch {}
  console.error('Tag syntax validation failed. See tags-error.json for details.');
  for (const i of issues) {
    console.error(`- ${i.file}: ${i.invalid.join(', ')}`);
  }
  process.exit(1);
} else {
  console.log('Tags syntax validation passed.');
}


