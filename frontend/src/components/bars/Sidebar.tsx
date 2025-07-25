import ExperimentList from "../experiment/ExperimentList.tsx";
import RunList from "../run/RunList.tsx";
import type {SidebarProps} from "../types/types.ts";


const Sidebar: React.FC<SidebarProps> = ({onSelectedExpId, onSelectedRunId, selectedExpId, selectedRunId}) => {
    return (
        <aside className="border border-gray-800 bg-gray-900/30">
            {/*paddings*/}
            <div className="p-4">
                <h2 className="text-md font-bold text-cyan-400 mb-1.5">Experiments</h2>
                <ExperimentList onSelectedExpId={onSelectedExpId} selectedExpId={selectedExpId}/>
            </div>
            {selectedExpId && (
                <div className="p-4">
                    <h2 className="text-md font-bold text-cyan-400 mb-1.5">Runs</h2>
                    <RunList experimentId={selectedExpId} onSelectedRunId={onSelectedRunId} selectedRunId={selectedRunId}/>
                </div>
            )}
        </aside>
    );
};

export default Sidebar;
