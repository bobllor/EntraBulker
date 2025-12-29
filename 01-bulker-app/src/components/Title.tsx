import {JSX} from "react";
import {VscAccount} from "react-icons/vsc";

export default function Title(): JSX.Element{
    return (
        <div className="flex fixed h-10 w-screen items-center justify-center top-10">
            <div className="flex items-center w-100 gap-1 text-2xl justify-center">
                <VscAccount /> 
                <span className="text-5xl text-center bg-transparent bg-gradient-to-tr from-blue-300 to-blue-700 
                bg-clip-text text-transparent">
                    EntraBulker    
                </span>
            </div> 
        </div>
    )
}