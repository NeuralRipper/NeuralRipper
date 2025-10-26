/**
 * Performance Metrics Calculations
 * Handles tokens/sec, TTFT (Time to First Token), runtime
 */

export interface PerformanceMetrics {
  tokensPerSec: number;
  ttft: number;        // milliseconds
  runtime: number;     // minutes
}

/**
 * Calculate tokens per second
 */
export const calculateTokensPerSec = (
  tokenCount: number,
  startTime: number,
  currentTime: number = Date.now()
): number => {
  if (tokenCount === 0 || startTime === 0) return 0;

  const elapsedSeconds = (currentTime - startTime) / 1000;
  if (elapsedSeconds === 0) return 0;

  return tokenCount / elapsedSeconds;
};

/**
 * Calculate Time to First Token (TTFT)
 */
export const calculateTTFT = (
  startTime: number,
  firstTokenTime: number
): number => {
  if (startTime === 0 || firstTokenTime === 0) return 0;
  return firstTokenTime - startTime;
};

/**
 * Calculate total runtime in minutes
 */
export const calculateRuntime = (
  startTime: number,
  currentTime: number = Date.now()
): number => {
  if (startTime === 0) return 0;

  const elapsedMs = currentTime - startTime;
  return elapsedMs / 1000 / 60; // Convert to minutes
};

/**
 * Get all performance metrics at once
 */
export const getPerformanceMetrics = (
  tokenCount: number,
  startTime: number,
  firstTokenTime: number,
  currentTime: number = Date.now()
): PerformanceMetrics => {
  return {
    tokensPerSec: calculateTokensPerSec(tokenCount, startTime, currentTime),
    ttft: calculateTTFT(startTime, firstTokenTime),
    runtime: calculateRuntime(startTime, currentTime),
  };
};
