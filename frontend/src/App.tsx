import Dashboard from "./components/Dashboard/Dashboard";
import Sidebar from "./components/Sidebar/Sidebar";
import {Routes, Route} from "react-router";

const App: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={
                <div className="bg-black min-h-screen w-full flex">
                    <Sidebar/>
                    <Dashboard/>
                </div>
            }/>
        </Routes>
    );
};

export default App;