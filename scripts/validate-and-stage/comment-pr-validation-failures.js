#!/usr/bin/env node

/**
 * Comment on PR with validation failure findings
 * 
 * Reads error JSON files and posts aggregated validation failures to the PR
 * 
 * Usage: comment-pr-validation-failures.js <owner> <repo> <pr_number>
 * 
 * Required environment variables:
 *   GITHUB_TOKEN - GitHub token for API authentication
 *   LARGE_FILES_JSON - JSON array of large files (optional)
 * 
 * Expected input files (optional):
 *   - folder-rename-error.json
 *   - multiple-md-error.json
 *   - validation-error.json
 *   - categories-error.json
 *   - frontmatter-error.json
 *   - profanity-report.json
 */

const fs = require('fs');
const https = require('https');

// Parse command line arguments
if (process.argv.length < 5) {
  console.error('Usage: comment-pr-validation-failures.js <owner> <repo> <pr_number>');
  console.error('Example: comment-pr-validation-failures.js myorg myrepo 123');
  process.exit(1);
}

const owner = process.argv[2];
const repo = process.argv[3];
const prNumber = process.argv[4];

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
if (!GITHUB_TOKEN) {
  console.error('Error: GITHUB_TOKEN environment variable is required');
  process.exit(1);
}

const sections = [];

// Collect all validation failures

// 1. Folder renames
if (fs.existsSync('folder-rename-error.json')) {
  try {
    const data = JSON.parse(fs.readFileSync('folder-rename-error.json', 'utf8'));
    if (data && data.type === 'folder_rename') {
      const renames = Array.isArray(data.renames) ? data.renames : [];
      if (renames.length) {
        const renameList = renames.map(r => `- \`${r.old_folder}\` → \`${r.new_folder}\``).join('\n');
        sections.push(`### 📁 Folder Rename Detected\n\n${data.message}\n\n${renameList}`);
      }
    }
  } catch (err) {
    console.error('Error reading folder-rename-error.json:', err.message);
  }
}

// 2. Large files
const largeFiles = JSON.parse(process.env.LARGE_FILES_JSON || '[]');
if (largeFiles.length > 0) {
  const fileList = largeFiles.map(f => `- \`${f}\``).join('\n');
  sections.push(`### 📦 Large Files Detected\n\nFiles larger than 1MB found:\n\n${fileList}\n\nYou have two options: \n 1. Reduce the file size(s) before merging (best for images); or \n 2. Move your file(s) into a folder beginning with an underscore (e.g., \`_large_files/\`). Note that in this case, your file will NOT be uploaded to snowflake.com, and you will have to [link to it directly](https://docs.github.com/en/repositories/working-with-files/using-files/getting-permanent-links-to-files). `);
}

// 3. Multiple markdown files
if (fs.existsSync('multiple-md-error.json')) {
  try {
    const data = JSON.parse(fs.readFileSync('multiple-md-error.json', 'utf8'));
    if (data && data.type === 'multiple_markdown_files') {
      const errors = Array.isArray(data.errors) ? data.errors : [];
      if (errors.length) {
        const lines = errors.map(err => `- **${err.folder}** (${err.files.length} files):\n${err.files.map(f => `  - \`${f}\``).join('\n')}`);
        sections.push(`### 📄 Multiple Markdown Files Detected\n\n${data.message}\n\n${lines.join('\n\n')}`);
      }
    }
  } catch (err) {
    console.error('Error reading multiple-md-error.json:', err.message);
  }
}

// 4. Language validation
if (fs.existsSync('validation-error.json')) {
  try {
    const v = JSON.parse(fs.readFileSync('validation-error.json', 'utf8'));
    if (v && v.type === 'language') {
      const items = Array.isArray(v.files) ? v.files.map(f => `- \`${f.file}\`: "${f.language || ''}"`).join('\n') : '';
      sections.push(`### 🌐 Language Validation Failed\n\n${v.message || 'Invalid or missing language detected. Allowed: en, es, it, fr, de, ja, ko, pt_br'}\n\n${items}`);
    }
  } catch (err) {
    console.error('Error reading validation-error.json:', err.message);
  }
}

// 5. Categories validation
if (fs.existsSync('categories-error.json')) {
  try {
    const data = JSON.parse(fs.readFileSync('categories-error.json', 'utf8'));
    const issues = Array.isArray(data.issues) ? data.issues : [];
    if (issues.length) {
      const lines = issues.map(issue => `- \`${issue.file}\`: ${(issue.invalid || []).join(', ')}`);
      sections.push(`### 🏷️ Category Syntax Validation Failed\n\nExpected categories like 'snowflake-site:taxonomy/x/y'.\n\n${lines.join('\n')}`);
    } else {
      sections.push(`### 🏷️ Category Syntax Validation Failed\n\nCategory syntax is invalid.`);
    }
  } catch (err) {
    console.error('Error reading categories-error.json:', err.message);
  }
}

// 6. Frontmatter validation
if (fs.existsSync('frontmatter-error.json')) {
  try {
    const data = JSON.parse(fs.readFileSync('frontmatter-error.json', 'utf8'));
    const issues = Array.isArray(data.issues) ? data.issues : [];
    if (issues.length) {
      const lines = issues.map(issue => `- \`${issue.file}\`: ${(issue.errors || []).join('; ')}`);
      sections.push(`### 📄 Frontmatter Validation Failed\n\nFrontmatter id must be slugified and match file and folder.\n\n${lines.join('\n')}`);
    } else {
      sections.push(`### 📄 Frontmatter Validation Failed\n\nFrontmatter id check failed.`);
    }
  } catch (err) {
    console.error('Error reading frontmatter-error.json:', err.message);
  }
}

// 7. Profanity validation
if (fs.existsSync('profanity-report.json')) {
  try {
    const data = JSON.parse(fs.readFileSync('profanity-report.json', 'utf8'));
    const issues = Array.isArray(data.issues) ? data.issues : [];
    if (data.error) {
      // Installation error
      sections.push(`### 🚫 Profanity Check Failed\n\n${data.error}`);
    } else if (issues.length) {
      // Abusive words found
      const lines = issues.map(issue => `- \`${issue.file}\`: ${(issue.words || []).join(', ')}`);
      sections.push(`### 🚫 Profanity Check Failed\n\nAbusive words detected:\n\n${lines.join('\n')}`);
    } else {
      // Empty issues array (shouldn't happen with refactored script, but handle gracefully)
      sections.push(`### 🚫 Profanity Check Failed\n\nProfanity check failed but no issues were listed.`);
    }
  } catch (err) {
    console.error('Error reading profanity-report.json:', err.message);
    sections.push(`### 🚫 Profanity Check Failed\n\nProfanity check encountered an error.`);
  }
}

// Build aggregated comment
if (sections.length === 0) {
  console.log('No validation failures found to report');
  process.exit(0);
}

const body = `## ⚠️ Validation Failed\n\n${sections.join('\n\n---\n\n')}\n\nPlease fix the issues above before merging.`;

// Post comment to GitHub
const postData = JSON.stringify({ body });

const options = {
  hostname: 'api.github.com',
  port: 443,
  path: `/repos/${owner}/${repo}/issues/${prNumber}/comments`,
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(postData),
    'Authorization': `Bearer ${GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github+json',
    'User-Agent': 'GitHub-Actions-Script'
  }
};

const req = https.request(options, (res) => {
  let responseData = '';

  res.on('data', (chunk) => {
    responseData += chunk;
  });

  res.on('end', () => {
    if (res.statusCode >= 200 && res.statusCode < 300) {
      console.log('✅ Successfully posted validation failure comment to PR');
      process.exit(0);
    } else {
      console.error(`❌ Failed to post comment. Status: ${res.statusCode}`);
      console.error('Response:', responseData);
      process.exit(1);
    }
  });
});

req.on('error', (error) => {
  console.error('❌ Error posting comment:', error.message);
  process.exit(1);
});

req.write(postData);
req.end();

