import Repository from "../portfolio/Repository.tsx";
import RunDetailCard from "../run/RunDetailCard.tsx";
import Sidebar from "../bars/Sidebar.tsx";
import Titlebar from "../bars/Titlebar.tsx";
import {useState} from "react";
import Rerun from "../run/Rerun.tsx";
import StreamingTerminal from "./Terminal.tsx";


const Dashboard: React.FC = () => {
    const [selectedExpId, setSelectedExpId] = useState("");
    const [selectedRunId, setSelectedRunId] = useState("");
    const [currentPage, setCurrentPage] = useState("home");

    return (
        <div className="font-cyber min-h-screen bg-gray-950 text-gray-100">
            <Titlebar onPageChange={setCurrentPage} />
            {/*flexible horizontally*/}
            {
                currentPage === "about" 
                ? <div className="flex justify-center"><Repository /></div>
                : currentPage === "home" ? <div className="flex">
                    <Sidebar
                        onSelectedExpId={setSelectedExpId}
                        onSelectedRunId={setSelectedRunId}
                        selectedExpId={selectedExpId}
                        selectedRunId={selectedRunId}
                    />
                    <main className="flex-1 bg-gray-900/30">
                        <div className="p-6">
                            <RunDetailCard selectedRunId={selectedRunId}/>
                        </div>
                    </main>
                </div> 
                : currentPage === "echo" ? <div className="flex">
                    <Rerun />
                </div>
                : currentPage === "infer" ? <StreamingTerminal /> 
                : <div>404</div>
                
            }
        </div>
    );
};

export default Dashboard;