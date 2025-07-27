import { API_BASE_URL } from "../../config";
import type {SingleMetricProps, MetricDetail} from "../types/types"
import { useEffect, useState } from "react";

const SingleMetricCard: React.FC<SingleMetricProps> = ({runId, metricName, finalValue}) => {
    const [history, setHistory] = useState<MetricDetail[]>([]);

    useEffect(() => {
        const fetchMetric = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/runs/metric/${runId}/${metricName}`)
                if (!response.ok) { 
                    console.log(`Failed to fetch metrics for run ${runId}`)
                    return; 
                }
                const data = await response.json();
                setHistory(data);
            } catch (error) {
                console.log(`Error loading ${metricName}. Error: ${error}`)
                return;
            }
        }

        fetchMetric();
    }, [runId, metricName])


    const firstValue = history[0]?.value;
    const trend = firstValue !== undefined && firstValue !== finalValue 
        ? (finalValue > firstValue ? "↗" : "↘") 
        : "";

    return (
        <div className="border rounded p-3 text-sm">
            <div className="flex justify-between items-center mb-1">
                <span className="font-medium">{metricName}</span>
                <span className="text-gray-600">
                    {finalValue?.toFixed(4)} {trend}
                </span>
            </div>
            
            <div className="text-xs text-gray-500">
                {history.length} points
                {firstValue !== undefined && firstValue !== finalValue && (
                    <span className="ml-2">
                        ({firstValue?.toFixed(4)} → {finalValue?.toFixed(4)})
                    </span>
                )}
            </div>
        </div>
    );
}


export default SingleMetricCard;