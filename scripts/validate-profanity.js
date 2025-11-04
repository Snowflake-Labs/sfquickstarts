#!/usr/bin/env node
/*
  Validate markdown files for abusive words using the 'bad-words' dictionary
  and a customizable blocklist provided via repository variable/secret.

  Inputs via env vars:
    - FILE_LIST_JSON: JSON array of file paths to scan
    - BLOCKLIST_STRING: optional newline- or comma-delimited words from repo variable
    - BLOCKLIST_SECRET_STRING: optional newline- or comma-delimited words from repo secret
*/

const fs = require('fs');
const path = require('path');

// We'll use a static list from 'badwords-list' to avoid ESM/CJS issues
function getBaseProfanityWords() {
  try {
    const bl = require('badwords-list');
    const arr = bl.array || bl.badwords || [];
    if (Array.isArray(arr)) return arr;
    return [];
  } catch (e) {
    console.error('Dependency "badwords-list" not installed.');
    return [];
  }
}

function readJsonEnvArray(envName) {
  try {
    const raw = process.env[envName] || '[]';
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch (e) {
    return [];
  }
}

function readBlocklistFromEnv() {
  const sources = [
    process.env.BLOCKLIST_STRING || '',
    process.env.BLOCKLIST_SECRET_STRING || '',
  ].filter(Boolean);
  if (sources.length === 0) return [];
  const combined = sources.join('\n');
  // Support newline- or comma-delimited lists, ignore comments starting with '#'
  return combined
    .split(/\r?\n|,/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && !l.startsWith('#'));
}

function tokenize(text) {
  // Extract alphanumeric words; keep accents via unicode classes if supported
  const matches = text.match(/[\p{L}\p{N}']+/gu) || [];
  return matches.map((w) => w.toLowerCase());
}

const files = readJsonEnvArray('FILE_LIST_JSON');
const extraWords = readBlocklistFromEnv();
const baseWords = getBaseProfanityWords().map((w) => String(w).toLowerCase());
const allWordsSet = new Set([...baseWords, ...extraWords.map((w) => w.toLowerCase())]);

const report = [];

for (const filePath of files) {
  if (!filePath.endsWith('.md')) continue;
  if (!fs.existsSync(filePath)) continue;
  const content = fs.readFileSync(filePath, 'utf8');
  const tokens = tokenize(content);
  const badSet = new Set();
  for (const t of tokens) {
    if (allWordsSet.has(t)) badSet.add(t);
  }
  if (badSet.size > 0) {
    report.push({ file: filePath, words: Array.from(badSet).sort() });
  }
}

// Write machine-readable report
try {
  fs.writeFileSync('profanity-report.json', JSON.stringify({ issues: report }, null, 2));
} catch (e) {
  // ignore
}

if (baseWords.length === 0) {
  console.error('Profanity base list unavailable. Ensure badwords-list is installed.');
  process.exit(2);
} else if (report.length > 0) {
  console.error('Abusive words detected in the following files:');
  for (const r of report) {
    console.error(`- ${r.file}: ${r.words.join(', ')}`);
  }
  process.exit(1);
} else {
  console.log('No abusive words found.');
}


