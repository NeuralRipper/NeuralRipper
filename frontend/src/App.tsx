import Dashboard from "./components/Dashboard/Dashboard";
import Sidebar from "./components/Sidebar/Sidebar";
import {Routes, Route} from "react-router";
import RunDetail from "./components/Run/RunDetail.tsx";

const App: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={
                <div className="bg-black min-h-screen w-full flex">
                    <Sidebar/>
                    <Dashboard/>
                </div>
            }/>
            <Route path="/runs/:runId" element={<RunDetail />}/>
        </Routes>
    );
};

export default App;