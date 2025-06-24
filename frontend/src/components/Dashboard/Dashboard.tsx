import ExperimentList from "../Experiment/ExperimentList";
import {useState} from "react";
import RunList from "../Run/RunList.tsx";
import RunDetailCard from "../Run/RunDetailCard.tsx";


const Dashboard: React.FC = () => {
    const [selectedExpId, setSelectedExpId] = useState("");
    const [selectedRunId, setSelectedRunId] = useState("");

    return (
        <div className="flex-1 p-5 min-h-screen">
            <h1 className="italic text-4xl font-mono font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-4 drop-shadow-[0_0_15px_rgba(34,211,238,0.5)]">
                NEURAL RIPPER
            </h1>
            <ExperimentList onSelectedExpId={setSelectedExpId}/>
            {selectedExpId && <RunList experimentId={selectedExpId} onSelectedRunId={setSelectedRunId}/>}
            {selectedRunId && <RunDetailCard selectedRunId={selectedRunId}/>}
        </div>
    );
};

export default Dashboard;