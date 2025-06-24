import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import {useNavigate} from "react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, Target, TrendingUp, BarChart3, Activity } from 'lucide-react';
import type {MetricList, MetricDetail, RunDetailCardProps} from "../types/types.ts";


const RunDetailCard: React.FC<RunDetailCardProps> = ({ selectedRunId }) => {
    const runId = selectedRunId;
    const [runData, setRunData] = useState(null);
    const [runMetricList, setRunMetricList] = useState<MetricList | null>(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
if (!runId) { return }
        if (!runId || runId === "") { return }

        const fetchAllData = async () => {
            setLoading(true);

            try {
                const [runResponse, metricsResponse] = await Promise.all([
                    fetch(`http://localhost:8000/runs/detail/${runId}`),
                    fetch(`http://localhost:8000/runs/metrics/${runId}`)
                ]);

                if (runResponse.ok) {
                    const runData = await runResponse.json();
                    setRunData(runData);
                }

                if (metricsResponse.ok) {
                    const metricList = await metricsResponse.json();
                    console.log("📊 Raw metrics from API:", metricList); // Debug log
                    setRunMetricList(metricList);
                }

            } catch (error) {
                console.error('Error during parallel fetch:', error);
            } finally {
                setLoading(false);
            }
        };

        if (runId) {
            fetchAllData();
        }
    }, [runId]);

    // 1. Group metrics by key (like groupby in pandas)
    const groupedMetrics = runMetricList?.metrics.reduce((acc, metric) => {
        if (!acc[metric.key]) {
            acc[metric.key] = [];
        }
        acc[metric.key].push({
            step: metric.step,        // epoch number
            value: metric.value,      // metric value
            timestamp: metric.timestamp
        });
        return acc;
    }, {} as Record<string, Array<{step: number, value: number, timestamp: number}>>) || {};

    // 2. Sort each metric group by step (epoch)
    Object.keys(groupedMetrics).forEach(key => {
        groupedMetrics[key].sort((a, b) => a.step - b.step);
    });

    console.log("📈 Grouped and sorted metrics:", groupedMetrics); // Debug log

    if (loading) {
        return (
            <div className="min-h-screen bg-black text-cyan-400 font-mono flex items-center justify-center">
                <div className="text-xl">Loading neural data...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-cyan-100 font-mono">
            {/* Header */}
            <div className="border-b border-cyan-500/30 bg-gray-900/90 p-6">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/')}
                        className="text-cyan-400 hover:text-cyan-300 transition-colors"
                    >
                        <ArrowLeft className="h-6 w-6" />
                    </button>

                    <div className="flex-1">
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                            {runData?.info?.run_name || 'Neural Run'}
                        </h1>
                        <div className="text-sm text-gray-400 mt-1">
                            Run ID: {runData?.info?.run_id}
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-8">
                {/* Overview Metric Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {runData?.data?.metrics?.train_accuracy && (
                        <div className="bg-gray-900/90 border border-green-500/40 rounded-lg p-4 hover:border-green-400/60 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-green-400 uppercase tracking-wide">Accuracy</span>
                                <Target className="h-4 w-4 text-green-400" />
                            </div>
                            <div className="text-2xl font-bold text-green-400">
                                {(runData.data.metrics.train_accuracy * 100).toFixed(2)}%
                            </div>
                        </div>
                    )}

                    {runData?.data?.metrics?.train_loss && (
                        <div className="bg-gray-900/90 border border-red-500/40 rounded-lg p-4 hover:border-red-400/60 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-red-400 uppercase tracking-wide">Loss</span>
                                <TrendingUp className="h-4 w-4 text-red-400" />
                            </div>
                            <div className="text-2xl font-bold text-red-400">
                                {runData.data.metrics.train_loss.toFixed(4)}
                            </div>
                        </div>
                    )}

                    {runData?.data?.params?.epochs && (
                        <div className="bg-gray-900/90 border border-blue-500/40 rounded-lg p-4 hover:border-blue-400/60 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-blue-400 uppercase tracking-wide">Epochs</span>
                                <BarChart3 className="h-4 w-4 text-blue-400" />
                            </div>
                            <div className="text-2xl font-bold text-blue-400">
                                {runData.data.params.epochs}
                            </div>
                        </div>
                    )}

                    {runData?.data?.params?.learning_rate && (
                        <div className="bg-gray-900/90 border border-purple-500/40 rounded-lg p-4 hover:border-purple-400/60 transition-colors">
                            <div className="flex items-center justify-between mb-2">
                                <span className="text-xs text-purple-400 uppercase tracking-wide">Learning Rate</span>
                                <Activity className="h-4 w-4 text-purple-400" />
                            </div>
                            <div className="text-2xl font-bold text-purple-400">
                                {runData.data.params.learning_rate}
                            </div>
                        </div>
                    )}
                </div>

                {/* 🎨 LAYER 5: Training Progress Charts */}
                {Object.keys(groupedMetrics).length > 0 && (
                    <div className="space-y-6">
                        <h3 className="text-cyan-400 font-bold text-lg uppercase tracking-wide">
                            Training Progress Over Epochs
                        </h3>

                        {/* 📊 Render a chart for each metric */}
                        {Object.entries(groupedMetrics).map(([metricName, metricHistory]) => (
                            <div key={metricName} className="bg-gray-900/90 border border-cyan-500/40 rounded-lg p-6">
                                <h4 className="text-cyan-400 font-bold mb-4 uppercase tracking-wide">
                                    {metricName.replace('_', ' ')} {/* train_accuracy → train accuracy */}
                                </h4>
                                <div className="h-64">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={metricHistory}>
                                            {/* Grid lines */}
                                            <CartesianGrid strokeDasharray="3 3" stroke="rgb(34 211 238 / 0.1)" />

                                            {/* X-axis (epochs) */}
                                            <XAxis
                                                dataKey="step"
                                                stroke="rgb(156 163 175)"
                                                tick={{ fontSize: 12 }}
                                                axisLine={{ stroke: 'rgb(34 211 238 / 0.3)' }}
                                            />

                                            {/* Y-axis (metric values) */}
                                            <YAxis
                                                stroke="rgb(156 163 175)"
                                                tick={{ fontSize: 12 }}
                                                axisLine={{ stroke: 'rgb(34 211 238 / 0.3)' }}
                                            />

                                            {/* Hover tooltip */}
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: 'rgb(17 24 39)',
                                                    border: '1px solid rgb(34 211 238)',
                                                    borderRadius: '8px',
                                                    color: 'rgb(34 211 238)',
                                                    fontSize: '12px'
                                                }}
                                                labelStyle={{ color: 'rgb(156 163 175)' }}
                                            />

                                            {/* The actual line */}
                                            <Line
                                                type="monotone"
                                                dataKey="value"
                                                stroke={
                                                    metricName.toLowerCase().includes('loss') ? "rgb(239 68 68)" :  // Red for loss
                                                    metricName.toLowerCase().includes('accuracy') ? "rgb(34 197 94)" :  // Green for accuracy
                                                    "rgb(34 211 238)"  // Cyan for others
                                                }
                                                strokeWidth={2}
                                                dot={false}  // No dots on data points
                                                activeDot={{
                                                    r: 4,
                                                    stroke: 'rgb(34 211 238)',
                                                    strokeWidth: 2,
                                                    fill: 'rgb(17 24 39)'
                                                }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Parameters Section */}
                <div className="bg-gray-900/90 border border-cyan-500/40 rounded-lg p-6">
                    <h3 className="text-cyan-400 font-bold text-lg mb-4 uppercase tracking-wide">
                        Run Parameters
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {runData && Object.entries(runData.data.params).map(([key, value]) => (
                            <div key={key} className="bg-gray-800/50 border border-gray-600/40 rounded p-3">
                                <div className="text-xs text-cyan-300 uppercase tracking-wide mb-1">{key}</div>
                                <div className="text-yellow-400 font-bold">{value}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Final Metrics Section */}
                {runMetricList && (
                    <div className="bg-gray-900/90 border border-cyan-500/40 rounded-lg p-6">
                        <h3 className="text-cyan-400 font-bold text-lg mb-4 uppercase tracking-wide">
                            Final Metrics
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {runData && Object.entries(runData.data.metrics).map(([key, value]) => (
                                <div key={key} className="bg-gray-800/50 border border-gray-600/40 rounded p-3">
                                    <div className="text-xs text-cyan-300 uppercase tracking-wide mb-1">
                                        {key.replace('_', ' ')}
                                    </div>
                                    <div className="text-green-400 font-bold text-lg">
                                        {typeof value === 'number' ? value.toFixed(4) : value}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default RunDetailCard;