#!/usr/bin/env node
/*
Merge generated redirects into site/firebase.json.

Usage:
  node site/tasks/helpers/merge_redirects_into_firebase.js \
    --firebase /absolute/path/to/site/firebase.json \
    --generated /absolute/path/to/site/firebase.redirects.generated.json
*/

const fs = require('fs');

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--firebase') out.firebase = args[++i];
    else if (a === '--generated') out.generated = args[++i];
  }
  if (!out.firebase || !out.generated) {
    console.error('Usage: node merge_redirects_into_firebase.js --firebase <file> --generated <file>');
    process.exit(1);
  }
  return out;
}

function loadJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function main() {
  const { firebase, generated } = parseArgs();
  const firebaseJson = loadJson(firebase);
  const generatedRedirects = loadJson(generated);

  if (!firebaseJson.hosting) firebaseJson.hosting = {};
  if (!Array.isArray(firebaseJson.hosting.redirects)) firebaseJson.hosting.redirects = [];

  const existing = firebaseJson.hosting.redirects;

  // Build a set of existing exact sources to avoid duplicates when merging
  const existingKey = new Set(
    existing
      .filter(r => r && typeof r.source === 'string' && !r.source.includes('{'))
      .map(r => `${r.source}=>${r.destination || r.type || ''}`)
  );

  let added = 0;
  for (const r of generatedRedirects) {
    const key = `${r.source}=>${r.destination || r.type || ''}`;
    if (existingKey.has(key)) continue;
    existing.push(r);
    existingKey.add(key);
    added++;
  }

  fs.writeFileSync(firebase, JSON.stringify(firebaseJson, null, 2) + '\n', 'utf8');
  console.log(`Merged ${added} redirects into ${firebase}`);
}

main();


