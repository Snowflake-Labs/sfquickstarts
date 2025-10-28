#!/usr/bin/env node
/*
Generate Firebase Hosting redirect entries from the SEO CSV mapping.

Input CSV (UTF-8): quickstarts-redirects.csv with columns:
  Old URL,Existing page status Code,New URL

Notes:
- Existing status code in CSV is informational only; we always emit final redirects per rules below.
- Destination URLs must include https:// and end with a trailing slash.
- Emit one brace-pattern rule per legacy base path: /path{,/**}.

Usage:
  node site/tasks/helpers/generate_firebase_redirects.js \
    --csv /absolute/path/to/quickstarts-redirects.csv \
    --out /absolute/path/to/site/firebase.redirects.generated.json
*/

const fs = require('fs');
const path = require('path');

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--csv') out.csv = args[++i];
    else if (a === '--out') out.out = args[++i];
    else if (a === '--status-default') out.statusDefault = args[++i];
  }
  if (!out.csv || !out.out) {
    console.error('Usage: node generate_firebase_redirects.js --csv <file> --out <file> [--status-default 301]');
    process.exit(1);
  }
  out.statusDefault = out.statusDefault || '301';
  return out;
}

function ensureHttpsAndSlash(urlLike) {
  if (!urlLike) return urlLike;
  let u = urlLike.trim();
  if (!u) return u;
  if (!u.startsWith('http://') && !u.startsWith('https://')) {
    u = 'https://' + u.replace(/^\/*/, '');
  }
  // Ensure trailing slash
  if (!u.endsWith('/')) {
    u += '/';
  }
  return u;
}

function toPathOnly(oldUrl) {
  const s = oldUrl.trim();
  try {
    const u = new URL(s);
    return u.pathname.replace(/\/+/g, '/');
  } catch (_) {
    // If it's already a path
    if (s.startsWith('/')) return s;
    // Try to coerce
    return '/' + s;
  }
}

function toBasePath(pathname) {
  if (!pathname) return pathname;
  let p = pathname;
  // Remove any trailing '/index.html'
  if (p.toLowerCase().endsWith('/index.html')) {
    p = p.slice(0, -('/index.html'.length));
  }
  // Remove trailing slash (but keep root '/')
  if (p.length > 1 && p.endsWith('/')) {
    p = p.slice(0, -1);
  }
  return p || '/';
}

function readCsv(filepath) {
  const raw = fs.readFileSync(filepath, 'utf8');
  const lines = raw.split(/\r?\n/).filter(Boolean);
  if (lines.length === 0) return [];
  const header = lines[0].split(',').map(h => h.trim());
  const idxOld = header.findIndex(h => /^old url$/i.test(h));
  const idxNew = header.findIndex(h => /^new url$/i.test(h));
  if (idxOld === -1 || idxNew === -1) {
    throw new Error('CSV must include columns: Old URL, New URL');
  }
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    // naive split: CSV appears simple (no commas in URLs); if needed, switch to a CSV parser
    const cols = line.split(',');
    if (cols.length < Math.max(idxOld, idxNew) + 1) continue;
    const oldUrl = cols[idxOld].trim();
    const newUrl = cols[idxNew].trim();
    if (!oldUrl || !newUrl) continue;
    rows.push({ oldUrl, newUrl });
  }
  return rows;
}

function buildRedirectEntries(rows, statusDefault) {
  const entries = [];
  const seen = new Set();
  const baseToDest = new Map();

  for (const { oldUrl, newUrl } of rows) {
    const dest = ensureHttpsAndSlash(newUrl);
    const oldPath = toPathOnly(oldUrl);
    const base = toBasePath(oldPath);

    // Special-case: avoid a root-wide catch-all from '/index.html' mapping
    if (base === '/' && /\/index\.html$/i.test(oldPath)) {
      const sources = ['/', '/index.html'];
      for (const source of sources) {
        const key = `${source}=>${dest}`;
        if (seen.has(key)) continue;
        seen.add(key);
        entries.push({ source, destination: dest, type: Number(statusDefault) });
      }
      continue;
    }

    // Use a single brace-pattern rule per base path
    const source = `${base}{,/**}`;
    baseToDest.set(source, dest);
  }

  for (const [source, dest] of baseToDest.entries()) {
    const key = `${source}=>${dest}`;
    if (seen.has(key)) continue;
    seen.add(key);
    entries.push({ source, destination: dest, type: Number(statusDefault) });
  }

  return entries;
}

function main() {
  const args = parseArgs();
  const rows = readCsv(args.csv);
  const redirects = buildRedirectEntries(rows, args.statusDefault);
  const outDir = path.dirname(args.out);
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(args.out, JSON.stringify(redirects, null, 2) + '\n', 'utf8');
  console.log(`Wrote ${redirects.length} redirects to ${args.out}`);
}

main();


