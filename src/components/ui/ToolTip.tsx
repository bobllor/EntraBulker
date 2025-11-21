import { JSX } from "react";
import { FaQuestion } from "react-icons/fa";

export function ToolTip({text}: {text: string}): JSX.Element{
    return (
        <>
            <span 
            title={text}
            className="mx-1 flex justify-center items-center rounded-2xl border-1 p-0.5 border-[#00488d]">
                <FaQuestion size={11} color="#00488d" /> 
            </span>
        </>
    )
}