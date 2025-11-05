#!/usr/bin/env node
/*
  Validate markdown front matter `id` and path consistency.

  Rules:
    - `id` must exist
    - `id` must be slugified: lowercase letters/digits separated by single dashes
      Pattern: ^[a-z0-9]+(?:-[a-z0-9]+)*$
    - `id` must match the markdown filename (without extension)
    - `id` must match the immediate folder name the file is in

  Inputs via env vars:
    - FILE_LIST_JSON: JSON array of file paths to scan
*/

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

function getFiles() {
  try {
    const raw = process.env.FILE_LIST_JSON || '[]';
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

function validateId(id) {
  const pattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  return pattern.test(String(id || ''));
}

const files = getFiles();
const issues = [];

for (const filePath of files) {
  if (!filePath.endsWith('.md')) continue;
  if (!fs.existsSync(filePath)) continue;
  const content = fs.readFileSync(filePath, 'utf8');

  let id;
  try {
    const fm = matter(content);
    id = fm?.data?.id;
  } catch {}
  // Fallback: scan first ~120 lines for a loose 'id:' key if YAML delimiters are missing
  if (!id) {
    const headLines = content.split(/\r?\n/, 120);
    const idx = headLines.findIndex((l) => /^\s*id\s*:/i.test(l));
    if (idx !== -1) {
      let after = headLines[idx].replace(/^\s*id\s*:/i, '').trim();
      // strip surrounding quotes if present
      if (/^".*"$/.test(after) || /^'.*'$/.test(after)) {
        after = after.slice(1, -1);
      }
      id = after;
    }
  }

  const fileName = path.basename(filePath, path.extname(filePath));
  const folderName = path.basename(path.dirname(filePath));

  const errors = [];
  if (!id) {
    errors.push('frontmatter id is missing');
  } else {
    const idStr = String(id);
    if (!validateId(idStr)) {
      errors.push('id must be slugified (lowercase letters/digits, single dashes)');
    }
    if (idStr !== fileName) {
      errors.push(`id must match filename ('${fileName}')`);
    }
    if (idStr !== folderName) {
      errors.push(`id must match folder name ('${folderName}')`);
    }
  }

  if (errors.length) {
    issues.push({ file: filePath, errors });
  }
}

if (issues.length) {
  try {
    fs.writeFileSync('frontmatter-error.json', JSON.stringify({ issues }, null, 2));
  } catch {}
  console.error('Frontmatter validation failed. See frontmatter-error.json for details.');
  for (const i of issues) {
    console.error(`- ${i.file}: ${i.errors.join('; ')}`);
  }
  process.exit(1);
} else {
  console.log('Frontmatter validation passed.');
}


