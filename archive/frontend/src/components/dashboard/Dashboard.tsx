import RunDetailCard from "../run/RunDetailCard.tsx";
import Sidebar from "../bars/Sidebar.tsx";
import Titlebar from "../bars/Titlebar.tsx";
import {useState} from "react";
import Portfolio from "../portfolio/Portfolio.tsx";
import EvalTerminal from "./EvalTerminal.tsx";


const Dashboard: React.FC = () => {
    const [selectedExpId, setSelectedExpId] = useState("");
    const [selectedRunId, setSelectedRunId] = useState("");
    const [currentPage, setCurrentPage] = useState("home");

    return (
        <div className="font-cyber h-screen bg-gray-950 text-gray-100 flex flex-col">
            <Titlebar onPageChange={setCurrentPage} />
            {/*flexible horizontally*/}
            <div className="flex-1 bg-gray-950">
                {
                    currentPage === "about" 
                    ? <div className="flex justify-center h-full"><Portfolio /></div>
                    : currentPage === "home" ? <div className="flex h-full">
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
                    : currentPage === "eval" ? <div className="w-full flex justify-center h-full p-1">
                        <EvalTerminal />
                    </div>
                    : <div>404</div>
                }
            </div>
        </div>
    );
};

export default Dashboard;