import ExperimentList from "../Experiment/ExperimentList";

const Dashboard: React.FC = () => {
    return (
        <div className="flex-1 p-5 min-h-screen">
            <h1 className="italic text-4xl font-mono font-bold bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-4 drop-shadow-[0_0_15px_rgba(34,211,238,0.5)]">
                NEURAL RIPPER
            </h1>
            <ExperimentList/>
        </div>
    );
};

export default Dashboard;