import ExperimentList from "../Experiment/ExperimentList";

const Dashboard: React.FC = () => {
    return (
        <div className="flex-1 p-6 min-h-screen">
            <h1 className="text-4xl font-mono font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent mb-4">
                NEURAL EXPERIMENTS
            </h1>
            <ExperimentList />
        </div>
    );
};

export default Dashboard;