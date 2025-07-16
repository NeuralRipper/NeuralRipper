import Dashboard from "./components/dashboard/Dashboard";
import {Routes, Route} from "react-router";

const App: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<Dashboard/>}/>
        </Routes>
    );
};

export default App;


// TODO: sort RunList inorder, running > finish > fail > time
// TODO: GCP compute engine, migrate container/image