#!/usr/bin/env node
/**
 * Notify - Tell the exercise tracker that Claude is ready
 * Used as a Claude Code hook
 */

const PORT = process.env.VIBEREPS_PORT || 8765;

fetch(`http://localhost:${PORT}/notify`, { method: 'POST' })
  .then(res => res.json())
  .then(data => console.log(JSON.stringify(data)))
  .catch(() => {
    // Tracker not running, that's fine
    console.log(JSON.stringify({ status: 'ok', message: 'Tracker not running' }));
  });
