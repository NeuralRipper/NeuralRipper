/**
 * Cost Calculation Utilities
 * Calculates inference costs based on token usage and model pricing
 */

// Pricing per 1000 tokens (example pricing - adjust based on your provider)
export const MODEL_PRICING: Record<string, { input: number; output: number }> = {
  'qwen': { input: 0.0001, output: 0.0002 },          // $0.0001 per 1k input tokens
  'llama-3-70b': { input: 0.0005, output: 0.001 },    // $0.0005 per 1k input tokens
  'gpt-4': { input: 0.03, output: 0.06 },             // Example
  'default': { input: 0.0001, output: 0.0002 },       // Fallback
};

/**
 * Calculate cost for token usage
 */
export const calculateTokenCost = (
  tokenCount: number,
  model: string,
  tokenType: 'input' | 'output' = 'output'
): number => {
  const pricing = MODEL_PRICING[model] || MODEL_PRICING['default'];
  const pricePerToken = pricing[tokenType] / 1000; // Convert per-1k to per-token

  return tokenCount * pricePerToken;
};

/**
 * Calculate total cost for input + output tokens
 */
export const calculateTotalCost = (
  inputTokens: number,
  outputTokens: number,
  model: string
): number => {
  const inputCost = calculateTokenCost(inputTokens, model, 'input');
  const outputCost = calculateTokenCost(outputTokens, model, 'output');

  return inputCost + outputCost;
};

/**
 * Calculate accumulated cost over time
 * Useful for live updates during streaming
 */
export const calculateAccumulatedCost = (
  previousCost: number,
  newTokens: number,
  model: string
): number => {
  const incrementalCost = calculateTokenCost(newTokens, model, 'output');
  return previousCost + incrementalCost;
};

/**
 * Format cost for display
 */
export const formatCost = (cost: number): string => {
  return `$${cost.toFixed(4)}`;
};
