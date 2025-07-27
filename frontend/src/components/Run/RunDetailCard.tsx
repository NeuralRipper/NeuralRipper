// RunDetailCard.tsx - Fixed version with correct colors and data retrieval
import {useEffect, useState} from "react";
import { Target, TrendingUp, BarChart3, Activity, Cpu } from 'lucide-react';
import type {RunDetailCardProps, Run} from '../types/types.ts';
import RunMetrics from './RunMetrics.tsx';
import MetricChart from './MetricChart.tsx';
import { API_BASE_URL } from "../../config.ts";
import type { MetricSummary } from "../types/types.ts";


const RunDetailCard: React.FC<RunDetailCardProps> = ({selectedRunId}) => {
    const [runData, setRunData] = useState<Run | null>(null);
    const [metricSummary, setMetricSummary] = useState<MetricSummary | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchRunDetail = async () => {
            if (!selectedRunId) return;
            
            setLoading(true);
            try {
                // Fetch run details
                const runResponse = await fetch(`${API_BASE_URL}/runs/detail/${selectedRunId}`);
                if (runResponse.ok) {
                    const runDataResult = await runResponse.json();
                    setRunData(runDataResult);
                }

                // Fetch metric names
                const metricResponse = await fetch(`${API_BASE_URL}/runs/metric-names/${selectedRunId}`);
                if (metricResponse.ok) {
                    const metricData = await metricResponse.json();
                    setMetricSummary(metricData);
                }
            } catch (error) {
                console.error('Error fetching run details:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchRunDetail();
    }, [selectedRunId]);

    if (loading) {
        return <div className="text-gray-500">Loading run details...</div>;
    }

    if (!runData) {
        return (
            <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                    <Cpu className="h-12 w-12 mx-auto mb-4 opacity-30"/>
                    <p>Select a run to view details</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Overview Metric Cards */}
            <div className={`grid grid-cols-2 gap-4 ${
                runData?.data?.metrics?.perplexity ? 'md:grid-cols-5' : 'md:grid-cols-4'
            }`}>
                {/* Conditional accuracy rendering: top5 for text models, regular for others */}
                {runData?.data?.metrics?.top5_accuracy ? (
                    <div className="bg-gray-800/50 rounded-lg p-4 hover:border border-emerald-400/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-emerald-400 tracking-wide">TOP-5 ACC</span>
                            <Target className="h-4 w-4 text-emerald-400"/>
                        </div>
                        <div className="text-2xl font-bold text-emerald-400">
                            {(runData.data.metrics.top5_accuracy * 100).toFixed(2)}%
                        </div>
                    </div>
                ) : runData?.data?.metrics?.train_accuracy && (
                    <div className="bg-gray-800/50 rounded-lg p-4 hover:border border-green-400/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-green-400 tracking-wide">ACCURACY</span>
                            <Target className="h-4 w-4 text-green-400"/>
                        </div>
                        <div className="text-2xl font-bold text-green-400">
                            {(runData.data.metrics.train_accuracy * 100).toFixed(2)}%
                        </div>
                    </div>
                )}

                {runData?.data?.metrics?.train_loss && (
                    <div className="bg-gray-800/50 rounded-lg p-4 hover:border border-red-400/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-red-400 tracking-wide">LOSS</span>
                            <TrendingUp className="h-4 w-4 text-red-400"/>
                        </div>
                        <div className="text-2xl font-bold text-red-400">
                            {runData.data.metrics.train_loss.toFixed(4)}
                        </div>
                    </div>
                )}

                {/* Text Model Specific: Perplexity (5th card for text models) */}
                {runData?.data?.metrics?.perplexity && (
                    <div className="bg-gray-800/50 rounded-lg p-4 hover:border border-orange-400/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-orange-400 tracking-wide">PERPLEXITY</span>
                            <Activity className="h-4 w-4 text-orange-400"/>
                        </div>
                        <div className="text-2xl font-bold text-orange-400">
                            {runData.data.metrics.perplexity.toFixed(2)}
                        </div>
                    </div>
                )}

                {runData?.data?.params?.epochs && (
                    <div className="bg-gray-800/50 rounded-lg p-4 hover:border border-blue-400/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-blue-400 tracking-wide">EPOCHS</span>
                            <BarChart3 className="h-4 w-4 text-blue-400"/>
                        </div>
                        <div className="text-2xl font-bold text-blue-400">
                            {runData.data.params.epochs}
                        </div>
                    </div>
                )}

                {runData?.data?.params?.learning_rate && (
                    <div className="bg-gray-800/50 rounded-lg p-4 hover:border border-purple-400/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-purple-400 tracking-wide">LEARNING RATE</span>
                            <Activity className="h-4 w-4 text-purple-400"/>
                        </div>
                        <div className="text-2xl font-bold text-purple-400">
                            {runData.data.params.learning_rate}
                        </div>
                    </div>
                )}
            </div>

            {/* RunMetrics component for parameter groups */}
            {runData && <RunMetrics runParams={runData.data.params}/>}

            {/* Training Progress Charts */}
            {metricSummary && metricSummary.metric_names.length > 0 && (
                <div>
                    <h3 className="text-cyan-400 font-mono font-bold text-md mb-3 uppercase tracking-wide">TRAINING PROGRESS OVER EPOCHS</h3>
                    <div className="grid grid-cols-3 gap-1 space-y-1">
                        {metricSummary.metric_names.map(metricName => (
                            <MetricChart 
                                key={metricName}
                                runId={selectedRunId}
                                metricName={metricName}
                                finalValue={metricSummary.final_values[metricName]}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default RunDetailCard;