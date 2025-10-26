/**
 * Benchmark Accuracy Calculations
 * Handles score calculations for different benchmark types
 */

/**
 * Calculate accuracy percentage
 */
export const calculateAccuracy = (correct: number, total: number): number => {
  if (total === 0) return 0;
  return (correct / total) * 100;
};

/**
 * Calculate F1 score
 * F1 = 2 * (precision * recall) / (precision + recall)
 */
export const calculateF1Score = (precision: number, recall: number): number => {
  if (precision + recall === 0) return 0;
  return (2 * precision * recall) / (precision + recall);
};

/**
 * Calculate precision
 * Precision = True Positives / (True Positives + False Positives)
 */
export const calculatePrecision = (
  truePositives: number,
  falsePositives: number
): number => {
  const total = truePositives + falsePositives;
  if (total === 0) return 0;
  return truePositives / total;
};

/**
 * Calculate recall
 * Recall = True Positives / (True Positives + False Negatives)
 */
export const calculateRecall = (
  truePositives: number,
  falseNegatives: number
): number => {
  const total = truePositives + falseNegatives;
  if (total === 0) return 0;
  return truePositives / total;
};

/**
 * Calculate average score across multiple benchmarks
 */
export const calculateAverageScore = (scores: number[]): number => {
  if (scores.length === 0) return 0;
  const sum = scores.reduce((acc, score) => acc + score, 0);
  return sum / scores.length;
};

/**
 * Format score for display
 */
export const formatScore = (score: number, decimals: number = 1): string => {
  return score.toFixed(decimals);
};
