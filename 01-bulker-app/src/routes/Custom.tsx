import React, { JSX, useEffect, useState } from "react";
import ManualForm from "../components/FormComponents/ManualForm";
import { handleDivClick } from "../components/FormComponents/manualUtils/functions";

export default function Custom({style, formState}: ManualProps): JSX.Element{
    const [selectedCell, setSelectedCell] = useState<string>('');
    const [editCell, setEditCell] = useState<string>('');

    // side effect when edit cell active -> inactive
    useEffect(() => {
        if(editCell == ""){
            setSelectedCell("");
        }
    }, [editCell])

    return (
        <>
            <div
            onClick={e => {
                editCell == "" && handleDivClick(e, selectedCell, setSelectedCell);
            }}
            className={style}>
                <ManualForm formState={formState} 
                selectState={{selectedCell: selectedCell, setSelectedCell: setSelectedCell}}
                editCellState={{setEditCell: setEditCell, editCell: editCell}} />
            </div>
        </>
    )
}

type ManualProps = {
    style: string,
    formState: {
        state: boolean,
        func: React.Dispatch<React.SetStateAction<boolean>>
    },
}