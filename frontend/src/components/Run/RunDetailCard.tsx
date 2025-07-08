import {CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from "recharts";
import {useEffect, useState} from "react";
import {Activity, BarChart3, Cpu, Target, TrendingUp} from 'lucide-react';
import type {MetricList, RunDetailCardProps} from "../types/types.ts";
import { API_BASE_URL } from "../../config.ts";
import RunMetrics from "./RunMetrics.tsx";


const RunDetailCard: React.FC<RunDetailCardProps> = ({selectedRunId}) => {
    const runId = selectedRunId;
    const [runData, setRunData] = useState(null);
    const [runMetricList, setRunMetricList] = useState<MetricList | null>(null);

    // TODO: reduce and clean up this file
    // TODO: RunList Status is not align with the date, fix it
    // TODO: remove the border of metrics and back the bg darker might help a lot
    // TODO: might need to separate the metrics, like loss, learning rate, acc,to make this cleaner
    // TODO: realtime update of the graph?

    useEffect(() => {
        if (!runId || runId === "") {
            return
        }

        const fetchAllData = async () => {
            try {
                const [runResponse, metricsResponse] = await Promise.all([
                    fetch(`${API_BASE_URL}/runs/detail/${runId}`),
                    fetch(`${API_BASE_URL}/runs/metrics/${runId}`)
                ]);

                if (runResponse.ok) {
                    const runData = await runResponse.json();
                    setRunData(runData);
                    console.log(runData)
                }

                if (metricsResponse.ok) {
                    const metricList = await metricsResponse.json();
                    console.log("Raw metrics from API:", metricList); // Debug log
                    setRunMetricList(metricList);
                }
            } catch (error) {
                console.error('Error during parallel fetch:', error);
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
    }, {} as Record<string, Array<{ step: number, value: number, timestamp: number }>>) || {};

    // 2. Sort each metric group by step (epoch)
    Object.keys(groupedMetrics).forEach(key => {
        groupedMetrics[key].sort((a, b) => a.step - b.step);
    });

    console.log("Grouped and sorted metrics:", groupedMetrics);

    if (!selectedRunId) {
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
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {runData?.data?.metrics?.train_accuracy && (
                    <div
                        className="bg-gray-800/50 rounded-lg p-4 hover:border border-green-400/60 transition-colors">
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
                    <div
                        className="bg-gray-800/50 rounded-lg p-4 hover:border border-red-400/60 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-red-400 tracking-wide">LOSS</span>
                            <TrendingUp className="h-4 w-4 text-red-400"/>
                        </div>
                        <div className="text-2xl font-bold text-red-400">
                            {runData.data.metrics.train_loss.toFixed(4)}
                        </div>
                    </div>
                )}

                {runData?.data?.params?.epochs && (
                    <div
                        className="bg-gray-800/50 rounded-lg p-4 hover:border border-blue-400/60 transition-colors">
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
                    <div
                        className="bg-gray-800/50 rounded-lg p-4 hover:border border-purple-400/60 transition-colors">
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

            {/* Parameters Section */}
            {runData && <RunMetrics runParams={runData.data.params}/>}

            <h3 className="text-cyan-400 font-bold text-lg uppercase tracking-wide">
                Training Progress Over Epochs
            </h3>
            {/* Training Progress Charts */}
            {Object.keys(groupedMetrics).length > 0 && (
                <div className="grid grid-cols-2 gap-1">
                    {/* Render a chart for each metric */}
                    {Object.entries(groupedMetrics).map(([metricName, metricHistory]) => (
                        <div key={metricName} className="bg-gray-800/50 rounded-lg p-6">
                            <h4 className="text-cyan-400 font-bold mb-4 uppercase tracking-wide">
                                {metricName.replace('_', ' ')} {/* train_accuracy → train accuracy */}
                            </h4>
                            <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={metricHistory}>
                                        {/* Grid lines */}
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgb(34 211 238 / 0.1)"/>

                                        {/* X-axis (epochs) */}
                                        <XAxis
                                            dataKey="step"
                                            stroke="rgb(156 163 175)"
                                            tick={{fontSize: 12}}
                                            axisLine={{stroke: 'rgb(34 211 238 / 0.3)'}}
                                        />

                                        {/* Y-axis (metric values) */}
                                        <YAxis
                                            stroke="rgb(156 163 175)"
                                            tick={{fontSize: 12}}
                                            axisLine={{stroke: 'rgb(34 211 238 / 0.3)'}}
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
                                            labelStyle={{color: 'rgb(156 163 175)'}}
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
        </div>
    );
};

export default RunDetailCard;