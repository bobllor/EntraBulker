import React, { JSX } from "react";
import { onDragDrop } from "./utils";
import { useFileContext } from "../../context/FileContext";

export default function DragZone({showDrop, setShowDrop}: DragZoneProps): JSX.Element{
    const {setUploadedFiles} = useFileContext();

    return (
        <div
        onDragEnter={e => {
            e.preventDefault();

            enableShowDrop(showDrop, setShowDrop);
        }}
        onDragLeave={e => {
            e.preventDefault();
            disableShowDrop(showDrop, setShowDrop);
        }}
        onDrop={e => {
            e.preventDefault();
            
            onDragDrop(e, setUploadedFiles);
            disableShowDrop(showDrop, setShowDrop);
        }}
        className={`absolute border-1 border-dashed bg-gray-300/60 blurs w-[80%] h-[75%] rounded-2xl
        ${!showDrop ? "opacity-0" : "opacity-100 z-4"} flex justify-center items-center`}>
            <span className="text-black text-3xl pointer-events-none">
                Drop file here
            </span>
        </div>
    )
}

function enableShowDrop(showDrop: boolean, setShowDrop: DragZoneProps["setShowDrop"]): void{
    if(!showDrop){
        setShowDrop(true);
    }
}

function disableShowDrop(showDrop: boolean, setShowDrop: DragZoneProps["setShowDrop"]): void{
    if(showDrop){
        setShowDrop(false);
    }
}

type DragZoneProps = {
    showDrop: boolean,
    setShowDrop: React.Dispatch<React.SetStateAction<boolean>>,
}