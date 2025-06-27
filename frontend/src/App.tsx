import Dashboard from "./components/Dashboard/Dashboard";
import {Routes, Route} from "react-router";

const App: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<Dashboard/>}/>
        </Routes>
    );
};

export default App;