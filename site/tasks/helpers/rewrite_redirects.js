#!/usr/bin/env node
/*
Rewrite site/firebase.json redirects to exactly [overrides + generated].

Usage:
  node site/tasks/helpers/rewrite_redirects.js \
    --firebase /absolute/path/to/site/firebase.json \
    --overrides /absolute/path/to/site/manual_redirect_overrides.json \
    --generated /absolute/path/to/site/firebase.redirects.generated.json
*/

const fs = require('fs');

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--firebase') out.firebase = args[++i];
    else if (a === '--overrides') out.overrides = args[++i];
    else if (a === '--generated') out.generated = args[++i];
  }
  if (!out.firebase || !out.overrides || !out.generated) {
    console.error('Usage: node rewrite_redirects.js --firebase <file> --overrides <file> --generated <file>');
    process.exit(1);
  }
  return out;
}

function uniqRedirects(list) {
  const seen = new Set();
  const out = [];
  for (const r of list) {
    const key = `${r.source}=>${r.destination||''}#${r.type||''}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(r);
  }
  return out;
}

function main() {
  const { firebase, overrides, generated } = parseArgs();
  const fb = JSON.parse(fs.readFileSync(firebase, 'utf8'));
  const ov = JSON.parse(fs.readFileSync(overrides, 'utf8'));
  const gen = JSON.parse(fs.readFileSync(generated, 'utf8'));

  if (!fb.hosting) fb.hosting = {};
  fb.hosting.redirects = uniqRedirects([...ov, ...gen]);

  fs.writeFileSync(firebase, JSON.stringify(fb, null, 2) + '\n', 'utf8');
  console.log(`Rewrote redirects: ${fb.hosting.redirects.length} total`);
}

main();


