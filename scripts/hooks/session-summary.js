#!/usr/bin/env node
/**
 * session-summary.js — Persist session activity summary
 *
 * Runs async at Stop. Tracks files edited, commands run, skills invoked.
 * Writes to .opc/sessions/ for cross-session continuity.
 */

const fs = require('fs');
const path = require('path');

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const sessionDir = path.join(process.cwd(), '.opc', 'sessions');
  const sessionFile = path.join(sessionDir, `session-${timestamp}.json`);

  const summary = {
    timestamp: new Date().toISOString(),
    tool_name: input.tool_name || 'unknown',
    session_id: process.env.CLAUDE_SESSION_ID || 'unknown'
  };

  try {
    if (!fs.existsSync(sessionDir)) {
      fs.mkdirSync(sessionDir, { recursive: true });
    }
    fs.writeFileSync(sessionFile, JSON.stringify(summary, null, 2));
  } catch (writeErr) {
    // Not critical
  }
} catch (e) {
  // Silent pass
}

process.exit(0);
