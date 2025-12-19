import React, { JSX, useRef } from "react";
import { useDismissRoute } from "../../hooks";

export default function BackgroundBlur({setComponentState = null}: {setComponentState: React.Dispatch<React.SetStateAction<boolean>> | null}): JSX.Element{
    const bgDivRef = useRef<HTMLDivElement>(null);

    if(setComponentState){
        useDismissRoute(bgDivRef, setComponentState);
    }

    return (
        <>
            <div ref={bgDivRef}
            className="bg-gray-300/40 backdrop-blur-2xl absolute w-full h-full z-3" />
        </>
    )    
}