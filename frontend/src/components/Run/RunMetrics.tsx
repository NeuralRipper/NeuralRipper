import type { SystemParamsProps } from "../types/types"
import { formatParamName, groupParameters } from "../utils/paramGrouping"

const RunMetrics: React.FC<SystemParamsProps> = ({ runParams }) => {
    // Parse and get the param list
    const groups = groupParameters(runParams)

    // PS: dynamically construct class names like hover:border-${group.color}, Tailwind's purger can't detect these classes at build time, so they get removed.
    // Map colors to complete class names
    const colorMap = {
        'blue-400': 'hover:border-blue-400',
        'green-400': 'hover:border-green-400', 
        'purple-400': 'hover:border-purple-400',
        'yellow-400': 'hover:border-yellow-400',
        'cyan-400': 'hover:border-cyan-400',
        'gray-400': 'hover:border-gray-400'
    }

    return (
        // IMPORTANT: grid with 2 columns for each group of params
        <div className="grid grid-cols-3 gap-3">
            {groups.map((group) => (
                <div key={group.title} className={`bg-gray-800/50 rounded-lg p-6 hover:border ${colorMap[group.color as keyof typeof colorMap]}`}>
                    <h3 className={`text-${group.color} font-bold text-lg mb-4 uppercase tracking-wide`}>
                        {group.title}
                    </h3>
                    {/* IMPORTANT: grid with 4 columns for all params */}
                    <div className="grid grid-cols-2 gap-1">
                        {Object.entries(group.params).map(([key, value]) => (
                            <div key={key} className="bg-gray-900/50 rounded p-0.5">
                                <div className="text-xs text-cyan-300 uppercase tracking-wide mb-1">
                                    {formatParamName(key)}
                                </div>
                                <div className="text-yellow-400 font-bold">
                                    {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}


export default RunMetrics;