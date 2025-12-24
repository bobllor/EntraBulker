import {JSX} from "react";
import {VscAccount} from "react-icons/vsc";

export default function Title(): JSX.Element{
    return (
        <div className="flex fixed h-10 w-screen items-center justify-center top-10">
            <div className="flex items-center w-100 gap-1 text-2xl justify-center">
                <VscAccount /> 
                <span className="text-5xl text-center text-blue-700 stroke-black">
                    EntraBulker    
                </span>
            </div> 
        </div>
    )
}