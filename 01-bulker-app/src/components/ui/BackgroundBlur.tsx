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
            className="bg-black/20 backdrop-blur-xs absolute w-full h-full z-3" />
        </>
    )    
}