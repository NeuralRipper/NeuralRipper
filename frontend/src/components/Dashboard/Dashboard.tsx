import RunDetailCard from "../Run/RunDetailCard.tsx";
import Sidebar from "../Sidebar/Sidebar.tsx";
import Titlebar from "../Sidebar/Titlebar.tsx";
import {useState} from "react";


const Dashboard: React.FC = () => {
    const [selectedExpId, setSelectedExpId] = useState("");
    const [selectedRunId, setSelectedRunId] = useState("");

    return (
        <div className="min-h-screen bg-gray-950 text-gray-100">
            <Titlebar/>
            {/*flexible horizontally*/}
            <div className="flex">
                <Sidebar
                    onSelectedExpId={setSelectedExpId}
                    onSelectedRunId={setSelectedRunId}
                    selectedExpId={selectedExpId}
                />
                <main className="flex-1 bg-gray-950">
                    <div className="p-6">
                        <RunDetailCard selectedRunId={selectedRunId}/>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Dashboard;