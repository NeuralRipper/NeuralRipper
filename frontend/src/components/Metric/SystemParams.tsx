import type { SystemParamsProps } from "../types/types"
import { formatParamName, groupParameters } from "../utils/paramGrouping"

const SystemParams: React.FC<SystemParamsProps> = ({ runParams }) => {
    // Parse and get the param list
    const groups = groupParameters(runParams)

    return (
        // IMPORTANT: grid with 2 columns for each group of params
        <div className="grid grid-cols-3 gap-3">
            {groups.map((group) => (
                <div key={group.title} className="bg-gray-800/50 rounded-lg p-6">
                    <h3 className={`${group.color} font-bold text-lg mb-4 uppercase tracking-wide`}>
                        {group.title}
                    </h3>
                    {/* IMPORTANT: grid with 4 columns for all params */}
                    <div className="grid grid-cols-3 gap-1">
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


export default SystemParams;