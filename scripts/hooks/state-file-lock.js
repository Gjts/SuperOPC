#!/usr/bin/env node
/**
 * state-file-lock.js — STATE.md File Lock (PreWrite Guard)
 *
 * Prevents parallel write conflicts on .opc/STATE.md during wave execution.
 * Uses a simple file-based lock (.opc/STATE.md.lock) with timeout.
 *
 * Behavior:
 * - If STATE.md is being written and a lock exists (< 30s old), warn the agent
 * - If lock is stale (> 30s), auto-release and allow
 * - On write completion, lock is released by the agent or times out
 *
 * This is an advisory guard — it warns but does not block.
 */

const fs = require('fs');
const path = require('path');

const LOCK_TIMEOUT_MS = 30000; // 30 seconds
const STATE_FILENAME = 'STATE.md';
const LOCK_SUFFIX = '.lock';

try {
  const raw = fs.readFileSync(0, 'utf8');
  const input = JSON.parse(raw);

  // Extract the file path being written
  const toolInput = input.tool_input || {};
  const filePath = toolInput.file_path || toolInput.path || '';

  // Only guard STATE.md writes
  if (!filePath || !path.basename(filePath).toUpperCase().startsWith('STATE')) {
    process.exit(0);
  }

  // Check if this is within an .opc/ directory
  const normalized = filePath.replace(/\\/g, '/');
  const isOpcState = normalized.includes('.opc/') || normalized.includes('.planning/');

  if (!isOpcState) {
    process.exit(0);
  }

  const lockPath = filePath + LOCK_SUFFIX;

  // Check for existing lock
  if (fs.existsSync(lockPath)) {
    try {
      const lockData = JSON.parse(fs.readFileSync(lockPath, 'utf8'));
      const lockAge = Date.now() - (lockData.timestamp || 0);

      if (lockAge < LOCK_TIMEOUT_MS) {
        // Active lock — warn the agent
        const lockAgeSec = Math.round(lockAge / 1000);
        const lockedBy = lockData.agent || 'unknown agent';

        const output = {
          hookSpecificOutput: {
            hookEventName: "PreToolUse",
            additionalContext:
              `STATE FILE LOCK WARNING: ${path.basename(filePath)} is currently locked by "${lockedBy}" ` +
              `(${lockAgeSec}s ago). Another agent may be writing to this file. ` +
              `To avoid conflicts, wait a few seconds and retry, or write to a different section. ` +
              `Lock will auto-expire after ${LOCK_TIMEOUT_MS / 1000}s.`
          }
        };

        process.stdout.write(JSON.stringify(output));
        process.exit(0);
      } else {
        // Stale lock — remove it
        try { fs.unlinkSync(lockPath); } catch (_) {}
      }
    } catch (_) {
      // Corrupted lock file — remove it
      try { fs.unlinkSync(lockPath); } catch (_) {}
    }
  }

  // Acquire lock
  const lockData = {
    timestamp: Date.now(),
    agent: input.agent_name || process.env.CLAUDE_SESSION_ID || 'unknown',
    file: path.basename(filePath)
  };

  try {
    const lockDir = path.dirname(lockPath);
    if (!fs.existsSync(lockDir)) {
      fs.mkdirSync(lockDir, { recursive: true });
    }
    fs.writeFileSync(lockPath, JSON.stringify(lockData, null, 2));
  } catch (_) {
    // Lock acquisition failed — not critical, continue
  }

  // Schedule lock release after timeout (best-effort)
  setTimeout(() => {
    try {
      if (fs.existsSync(lockPath)) {
        const current = JSON.parse(fs.readFileSync(lockPath, 'utf8'));
        if (current.timestamp === lockData.timestamp) {
          fs.unlinkSync(lockPath);
        }
      }
    } catch (_) {}
    process.exit(0);
  }, LOCK_TIMEOUT_MS);

} catch (_) {
  // Silent fail — never block writes
  process.exit(0);
}
