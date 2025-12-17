import { JSX } from "react";

export default function ProgressBar({innerProgressBarWidth}: ProgressBarProps): JSX.Element{
    return (
        <>
            <div className="w-full h-10 flex justify-center items-center">
                <div className="bg-gray-500 w-[90%] h-5 rounded-2xl flex items-center justify-start p-2 default-shadow">
                    { /* The progress bar */}
                    <div className="bg-blue-300 h-4 rounded-2xl"
                    style={{width: `${innerProgressBarWidth}%`}} />
                </div> 
            </div> 
        </>
    )
}

type ProgressBarProps = {
    innerProgressBarWidth: number,
}