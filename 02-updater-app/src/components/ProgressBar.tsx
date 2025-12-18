import { JSX } from "react";

export default function ProgressBar({innerProgressBarWidth, failed = false}: ProgressBarProps): JSX.Element{
    return (
        <>
            <div className="w-full h-10 flex justify-center items-center">
                <div className="bg-gray-400 w-[90%] h-5 rounded-2xl flex items-center justify-start default-shadow">
                    { /* The progress bar */}
                    <div className={`${!failed ? "bg-green-600" : "bg-red-800"} w-[inherit] h-[inherit] rounded-2xl`}
                    style={{width: `${innerProgressBarWidth}%`}} />
                </div> 
            </div> 
        </>
    )
}

type ProgressBarProps = {
    innerProgressBarWidth: number,
    failed?: boolean,
}