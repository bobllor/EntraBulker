import React, { JSX, useEffect, useRef } from "react";
import { ManualData } from "./manualUtils/types";
import { toastError } from "../../toastUtils";
import { FaTimes, FaCheck } from "react-icons/fa";

const buttonClass: string = "hover:bg-gray-400 p-2 rounded-xl";

/** Component of ManualTable that reveals an edit box for a selected cell. */
export default function EditCell({id, stringVal, setEditCell, manData, checkEmpty = false}: EditCellProps): JSX.Element{
    const inputRef = useRef<HTMLInputElement|null>(null);
    
    useEffect(() => {
        if(inputRef.current){
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, [])
    
    return (
        <>
            <div
            className="absolute h-12 z-4 bg-white border-1 border-black/40 rounded-2xl p-4 flex justify-center items-center gap-5">
                <input className="py-1 px-2 rounded-xl w-35 input-style"
                spellCheck={false}
                ref={inputRef}
                type="text" 
                defaultValue={stringVal} 
                onKeyDown={(e) => {
                    if(e.key == 'Escape') setEditCell('');

                    if(e.key == 'Enter'){
                        const inputVal: string = e.currentTarget.value;
                        
                        if(inputVal.trim() == stringVal){
                            setEditCell('');
                        }else{
                            editManualEntry(inputRef, id, manData, checkEmpty).then(status => {
                                if(status){
                                    setEditCell("");
                                }
                            })
                        };
                    }
                }}/>
                <div
                className="flex gap-1">
                    <span 
                    onClick={() => editManualEntry(inputRef, id, manData, checkEmpty).then(
                        (status) => {
                            if(status){
                                setEditCell('');
                            }
                        })
                    }
                    className={buttonClass}>
                        <FaCheck color="green" />
                    </span>
                    <span
                    className={buttonClass}
                    onClick={() => setEditCell('')}>
                        <FaTimes color="red" />
                    </span>
                </div>
            </div>
        </>
    )
}

type EditCellProps = {
    id: string,
    stringVal: string,
    setEditCell: React.Dispatch<React.SetStateAction<string>>,
    manData: ManDataProps,
    checkEmpty?: boolean,
}

type ManDataProps = {
    manualData: Array<ManualData>
    setManualData: React.Dispatch<React.SetStateAction<Array<ManualData>>>
}

/**
 * Edits an existing manual entry and updates the state.
 * @param inputRef The ref object of the input element.
 * @param cellId The ID of the current component.
 * @param manData The manual data state and function object.
 * @param checkEmpty Boolean to prevent the cell from being empty. If false, then it will accept empty values.
 * This is also used to determine if the editing cell is the Name field or the Organization (opco) field.
 * @returns A boolean Promise.
 */
async function editManualEntry(inputRef: React.RefObject<HTMLInputElement|null>, cellId: string, manData: ManDataProps, checkEmpty: boolean): Promise<boolean>{
    if(inputRef.current == null){
        return false;
    }

    const value: string = inputRef.current.value.trim();

    if(value == "" && checkEmpty){
        toastError("Cannot have empty value");
    
        return false;
    }

    // NOTE: the cellId is NOT the same as the id inside the manual data.
    // according to a previous note by me (june 2025): id = obj.id + obj.name, easy way to diff the two columns
    // string.includes() must be used. thanks me!
    const idData: ManualData = {...manData.manualData.filter((man) => (cellId.includes(man.id!)))[0]};

    const checkDuplicate = (data: string, otherData: string) => {
        if(data == otherData){
            toastError("Cannot have duplicate values");
            return false;
        }

        return true;
    }

    if(checkEmpty){
        if(!checkDuplicate(value, idData.opco!)) return false;

        idData.name = value;
    }else{
        if(!checkDuplicate(value, idData.name!)) return false;

        idData.opco = value;
    }

    manData.setManualData(prev => prev.map((ele) => {
        if(cellId.includes(ele.id!)){
            return {...idData, id: ele.id};
        }

        return {...ele};
    }))

    return true;
}