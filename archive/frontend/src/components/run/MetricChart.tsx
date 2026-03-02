import {useEffect, useState} from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { API_BASE_URL } from "../../config.ts";
import type { MetricChartProps, MetricDetail } from "../types/types.ts";

const MetricChart: React.FC<MetricChartProps> = ({runId, metricName, finalValue}) => {
    const [history, setHistory] = useState<MetricDetail[]>([]);

    useEffect(() => {
        const fetchMetric = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/runs/metric/${runId}/${metricName}`);
                if (!response.ok) {
                    console.log(`Failed to load ${metricName}`);
                    return;
                } else {
                    
                    const data = await response.json();
                    setHistory(data);
                }
            } catch (err) {
                console.log(`Error loading ${metricName}`);
                return;
            }
        };

        fetchMetric();

        // Fetch new epoch data every 10 seconds
        const intervalId = setInterval(() => {
            console.log("Epoch data updated.");
            fetchMetric();
        }, 10000)

        return () => clearInterval(intervalId);
    }, [runId, metricName]);

    // Prepare chart data
    const chartData = history.map(point => ({
        step: point.step,
        value: point.value,
        timestamp: point.timestamp
    })).sort((a, b) => a.step - b.step);

    return (
        <div className="bg-gray-800/50 rounded-lg justify-center flex-col items-center p-3">
            <h4 className="text-cyan-400 text-sm font-bold mb-1.5 uppercase tracking-wide">
                {metricName.replace('_', ' ')}
            </h4>
            <div className="w-full h-48">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgb(34 211 238 / 0.1)"/>
                            <XAxis
                                dataKey="step"
                                stroke="rgb(156 163 175)"
                                tick={{fontSize: 12}}
                                axisLine={{stroke: 'rgb(34 211 238 / 0.3)'}}
                            />
                            <YAxis
                                stroke="rgb(156 163 175)"
                                tick={{fontSize: 12}}
                                axisLine={{stroke: 'rgb(34 211 238 / 0.3)'}}
                            />
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
                            <Line
                                type="monotone"
                                dataKey="value"
                                stroke={
                                    metricName.toLowerCase().includes('loss') ? "rgb(239 68 68)" :  // Red for loss
                                    metricName.toLowerCase().includes('perplexity') ? "rgb(251 146 60)" :  // Orange for perplexity
                                    metricName.toLowerCase().includes('accuracy') && metricName.toLowerCase().includes('top5') ? "rgb(16 185 129)" :  // Emerald for top5
                                    metricName.toLowerCase().includes('accuracy') ? "rgb(34 197 94)" :  // Green for regular accuracy
                                    metricName.toLowerCase().includes('learning') ? "rgb(168 85 247)" :  // Purple for learning rate
                                    "rgb(34 211 238)"  // Cyan for others
                                }
                                strokeWidth={2}
                                dot={false}
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
            <div className="text-xs text-cyan-300 mt-1">
                {history.length} data points ({finalValue?.toFixed(4)})
            </div>
        </div>
    );
};

export default MetricChart;