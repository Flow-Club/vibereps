#!/usr/bin/env node
/**
 * Stats - Combine code stats (from ccusage) with exercise stats
 */

import { execSync } from 'node:child_process';

async function getCodeStats() {
  try {
    const output = execSync('npx ccusage@latest --json', {
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return JSON.parse(output);
  } catch (e) {
    console.error('Could not get code stats from ccusage:', e.message);
    return null;
  }
}

async function getExerciseStats() {
  // TODO: Read from local storage or Prometheus
  // For now, return placeholder
  return {
    totalReps: 0,
    totalSessions: 0,
    byExercise: {},
  };
}

async function main() {
  console.log('📊 Fetching stats...\n');

  const [codeStats, exerciseStats] = await Promise.all([
    getCodeStats(),
    getExerciseStats(),
  ]);

  if (codeStats) {
    console.log('💻 Code Stats (from ccusage):');
    console.log(JSON.stringify(codeStats, null, 2));
  }

  console.log('\n💪 Exercise Stats:');
  console.log(JSON.stringify(exerciseStats, null, 2));

  // Combined summary
  console.log('\n📈 Combined:');
  console.log({
    code: codeStats ? 'loaded' : 'unavailable',
    exercises: exerciseStats,
  });
}

main();
