import ExperimentList from "../Experiment/ExperimentList.tsx";
import RunList from "../Run/RunList.tsx";
import type {SidebarProps} from "../types/types.ts";


const Sidebar: React.FC<SidebarProps> = ({onSelectedExpId, onSelectedRunId, selectedExpId}) => {
    return (
        <aside className="border border-gray-800 bg-gray-900/50">
            {/*paddings*/}
            <div className="p-4">
                <h2 className="text-md font-semibold text-cyan-400 mb-3">Experiments</h2>
                <ExperimentList onSelectedExpId={onSelectedExpId} selectedExpId={selectedExpId}/>
            </div>
            {selectedExpId && (
                <div className="p-4">
                    <h2 className="text-md font-semibold text-cyan-400 mb-3">Runs</h2>
                    <RunList experimentId={selectedExpId} onSelectedRunId={onSelectedRunId}/>
                </div>
            )}
        </aside>
    );
};

export default Sidebar;