#!/usr/bin/env node
/**
 * git-push-reminder.js — Remind to review before git push
 *
 * Advisory (exit 0). Source: ECC git-push-reminder pattern.
 */

const fs = require('fs');

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);
  const command = (input.tool_input && input.tool_input.command) || '';

  if (/\bgit\s+push\b/.test(command)) {
    console.log(
      'SuperOPC: About to push. Checklist:\n' +
      '  1. Tests pass?\n' +
      '  2. No debug statements left?\n' +
      '  3. Commit messages follow Conventional Commits?\n' +
      '  4. No secrets in committed files?'
    );
  }
} catch (e) {
  // Silent pass
}

process.exit(0);
