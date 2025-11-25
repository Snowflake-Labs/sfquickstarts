#!/usr/bin/env node
/*
  Validate 'categories' in markdown front matter. Accepts categories in either
  array form or comma-separated string. Each category must match:
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

function toArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value.map(String);
  const s = String(value);
  return s.split(/[\,\n]/).map((t) => t.trim()).filter(Boolean);
}

function extractCategories(content) {
  try {
    const fm = matter(content);
    const fmCats = toArray(fm?.data?.categories);
    if (fmCats.length) return fmCats;
  } catch {}

  const head = content.split(/\r?\n/, 120);
  const idx = head.findIndex((l) => /^\s*categories\s*:/i.test(l));
  if (idx === -1) return [];

  const line = head[idx];
  const afterColon = line.replace(/^\s*categories\s*:/i, '').trim();
  if (afterColon) {
    return afterColon.split(',').map((t) => t.trim()).filter(Boolean);
  }

  const categories = [];
  for (let i = idx + 1; i < head.length; i++) {
    const l = head[i];
    if (/^\s*-\s+/.test(l)) {
      categories.push(l.replace(/^\s*-\s+/, '').trim());
      continue;
    }
    if (categories.length && (/^\s*$/.test(l) || /^\s*\w[\w\- ]*\s*:\s*.*$/.test(l))) break;
  }
  return categories.filter(Boolean);
}

const CATEGORY_PATTERN = /^snowflake-site:taxonomy\/[a-z0-9][a-z0-9-]*(?:\/[a-z0-9][a-z0-9-]*)*$/;

const files = getFiles();
const issues = [];

for (const filePath of files) {
  if (!filePath.endsWith('.md')) continue;
  if (!fs.existsSync(filePath)) continue;
  const content = fs.readFileSync(filePath, 'utf8');
  const categories = extractCategories(content);
  if (!categories.length) continue; // no categories is not an error in this check
  const invalid = categories.filter((t) => !CATEGORY_PATTERN.test(String(t).trim().toLowerCase()));
  if (invalid.length) {
    issues.push({ file: filePath, invalid });
  }
}

if (issues.length) {
  try {
    fs.writeFileSync('categories-error.json', JSON.stringify({ issues }, null, 2));
  } catch {}
  console.error('Category syntax validation failed. See categories-error.json for details.');
  for (const i of issues) {
    console.error(`- ${i.file}: ${i.invalid.join(', ')}`);
  }
  process.exit(1);
} else {
  console.log('Categories syntax validation passed.');
}


