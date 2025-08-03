import Repository from "./Repository";

const Portfolio = () => {
    return (
        <div>
            <div className="flex justify-center p-10">
                <img src="../../assets/avatar.jpeg" className=" w-32 h-32 rounded-full object-cover"></img>
            </div>
            <div className="flex-col">
                <Repository />
            </div>
        </div>
    )
}

export default Portfolio;
