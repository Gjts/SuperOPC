#!/usr/bin/env node
/**
 * doc-file-warning.js — Warn about non-standard documentation files
 *
 * Advisory (exit 0). Warns when creating documentation files outside
 * recognized paths to keep project structure clean.
 */

const fs = require('fs');
const path = require('path');

const RECOGNIZED_DOCS = [
  'README.md', 'CONTRIBUTING.md', 'CHANGELOG.md', 'SECURITY.md',
  'LICENSE', 'CLAUDE.md', 'AGENTS.md', 'ROADMAP.md',
  'CODE_OF_CONDUCT.md', 'ARCHITECTURE.md'
];

const RECOGNIZED_DIRS = [
  'docs/', 'skills/', 'agents/', 'commands/', '.opc/'
];

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const filePath = (input.tool_input && (input.tool_input.file_path || input.tool_input.path)) || '';

  if (!filePath || !filePath.endsWith('.md')) {
    process.exit(0);
  }

  const basename = path.basename(filePath);
  const isRecognized = RECOGNIZED_DOCS.includes(basename) ||
    RECOGNIZED_DIRS.some(dir => filePath.includes(dir));

  if (!isRecognized) {
    console.log(
      'SuperOPC: Creating "' + basename + '" outside standard paths. ' +
      'Consider placing docs in docs/, skills in skills/, or using a recognized root file.'
    );
  }
} catch (e) {
  // Silent pass
}

process.exit(0);
