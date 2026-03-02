/**
 * Benchmark Progress Tracking
 * Handles progress calculations for benchmark tasks
 */

import type { Benchmark, BenchmarkStatus } from '../../types/eval';

/**
 * Calculate progress percentage
 */
export const calculateProgress = (current: number, total: number): number => {
  if (total === 0) return 0;
  return Math.min(100, (current / total) * 100);
};

/**
 * Update benchmark progress
 */
export const updateBenchmarkProgress = (
  benchmark: Benchmark,
  current: number
): Benchmark => {
  const progress = calculateProgress(current, benchmark.total);

  // Auto-update status based on progress
  let status: BenchmarkStatus = benchmark.status;
  if (progress >= 100) {
    status = 'done';
  } else if (progress > 0) {
    status = 'running';
  }

  return {
    ...benchmark,
    current,
    progress,
    status,
  };
};

/**
 * Create initial benchmark state
 */
export const createBenchmark = (
  name: string,
  total: number,
  status: BenchmarkStatus = 'queued'
): Benchmark => {
  return {
    name,
    total,
    current: 0,
    progress: 0,
    status,
  };
};

/**
 * Render progress bar (terminal style)
 */
export const renderProgressBar = (progress: number, width: number = 20): string => {
  const filled = Math.floor((progress / 100) * width);
  const empty = width - filled;
  return '█'.repeat(filled) + '░'.repeat(empty);
};

/**
 * Get status display text
 */
export const getStatusDisplay = (status: BenchmarkStatus): string => {
  const statusMap: Record<BenchmarkStatus, string> = {
    'queued': 'WAIT',
    'running': 'RUN ',
    'done': 'DONE',
    'error': 'ERR ',
  };
  return statusMap[status];
};
