#!/usr/bin/env node
/*
Prepend manual override redirects to Firebase config so they take precedence.

Usage:
  node site/tasks/helpers/insert_overrides.js \
    --firebase /absolute/path/to/site/firebase.json \
    --overrides /absolute/path/to/site/manual_redirect_overrides.json
*/

const fs = require('fs');

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--firebase') out.firebase = args[++i];
    else if (a === '--overrides') out.overrides = args[++i];
  }
  if (!out.firebase || !out.overrides) {
    console.error('Usage: node insert_overrides.js --firebase <file> --overrides <file>');
    process.exit(1);
  }
  return out;
}

function main() {
  const { firebase, overrides } = parseArgs();
  const fb = JSON.parse(fs.readFileSync(firebase, 'utf8'));
  const ov = JSON.parse(fs.readFileSync(overrides, 'utf8'));

  if (!fb.hosting) fb.hosting = {};
  if (!Array.isArray(fb.hosting.redirects)) fb.hosting.redirects = [];

  // Remove any existing entries with these sources to avoid duplicates, then prepend
  const sources = new Set(ov.map(r => r.source));
  fb.hosting.redirects = fb.hosting.redirects.filter(r => !sources.has(r.source));
  fb.hosting.redirects = [...ov, ...fb.hosting.redirects];

  fs.writeFileSync(firebase, JSON.stringify(fb, null, 2) + '\n', 'utf8');
  console.log(`Inserted ${ov.length} override redirects at the top of ${firebase}`);
}

main();


