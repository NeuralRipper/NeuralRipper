import Dashboard from "./components/Dashboard/Dashboard";
import Sidebar from "./components/Sidebar/Sidebar";


const App: React.FC = () => {
    return (
        <div className="bg-black min-h-screen w-full flex">
            <Sidebar/>
            <Dashboard/>
        </div>
    );
};

export default App;