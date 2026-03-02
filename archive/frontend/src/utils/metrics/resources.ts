/**
 * Resource Metrics Calculations
 * Handles GPU utilization, temperature, memory usage
 */

export interface ResourceMetrics {
  gpuUtil: number;      // percentage (0-100)
  temp: number;         // Celsius
  memoryUsed?: number;  // Optional: MB or GB
}

/**
 * Calculate GPU utilization percentage
 * In real implementation, this would come from backend metrics
 * For now, returns a placeholder value
 */
export const calculateGPUUtilization = (
  // These parameters would come from your backend/Modal metrics
  currentLoad?: number,
  maxLoad?: number
): number => {
  // Placeholder implementation
  // In production, you'd receive this from your backend
  if (currentLoad === undefined || maxLoad === undefined) {
    return 0; // Default when no data available
  }

  if (maxLoad === 0) return 0;
  return Math.min(100, (currentLoad / maxLoad) * 100);
};

/**
 * Get GPU temperature
 * In real implementation, this would come from backend metrics
 */
export const getGPUTemperature = (tempCelsius?: number): number => {
  // Placeholder implementation
  // In production, you'd receive this from your backend
  return tempCelsius ?? 0;
};

/**
 * Get all resource metrics at once
 */
export const getResourceMetrics = (
  gpuUtilization?: number,
  temperature?: number,
  memoryUsed?: number
): ResourceMetrics => {
  return {
    gpuUtil: gpuUtilization ?? 0,
    temp: temperature ?? 0,
    memoryUsed,
  };
};
