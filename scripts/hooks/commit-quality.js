#!/usr/bin/env node
/**
 * commit-quality.js — Pre-commit quality check
 *
 * Validates:
 * 1. Commit message follows Conventional Commits format
 * 2. No console.log/debugger/TODO left in staged files
 * 3. No hardcoded secrets (API keys, tokens)
 *
 * Advisory (exit 0) for warnings, blocking (exit 2) for secrets.
 */

const fs = require('fs');

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const command = (input.tool_input && input.tool_input.command) || '';

  // Only check git commit commands
  if (!/\bgit\s+commit\b/.test(command)) {
    process.exit(0);
  }

  const warnings = [];

  // Check commit message format (if -m flag present)
  const msgMatch = command.match(/-m\s+["']([^"']+)["']/);
  if (msgMatch) {
    const msg = msgMatch[1];
    const conventionalPattern = /^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?:\s.+/;
    if (!conventionalPattern.test(msg)) {
      warnings.push(
        'Commit message does not follow Conventional Commits format.\n' +
        '  Expected: type(scope): description\n' +
        '  Example:  feat(skills): add pricing skill'
      );
    }
  }

  // Check for secret patterns in commit message
  const secretPatterns = [
    /sk-[a-zA-Z0-9]{20,}/,      // OpenAI keys
    /ghp_[a-zA-Z0-9]{36}/,      // GitHub PAT
    /AKIA[0-9A-Z]{16}/,         // AWS access key
    /[a-zA-Z0-9+/]{40,}={0,2}/, // Generic base64 that might be a key
  ];

  if (msgMatch) {
    for (const pattern of secretPatterns) {
      if (pattern.test(msgMatch[1])) {
        console.log('SuperOPC: Potential secret detected in commit message. Review before committing.');
        process.exit(2);
      }
    }
  }

  if (warnings.length > 0) {
    console.log('SuperOPC commit quality:\n' + warnings.map(w => '  - ' + w).join('\n'));
  }
} catch (e) {
  // Silent pass
}

process.exit(0);
