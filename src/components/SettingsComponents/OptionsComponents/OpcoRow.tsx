import React, { JSX, useRef } from "react";
import { OpcoMap } from "../types";
import { useResetOpcoValues } from "../hooks";
import { toastError } from "../../../toastUtils";
import { checkRes } from "../../../utils";
import "../../../pywebview";
import { FaTrash } from "react-icons/fa";

const DEFAULT_KEY: string = "default";

export default function OpcoRow(
    {opco, baseOpco, isEditable, setOpcoOptions, defaultResetProp, setUpdateBaseRef, partialResetProp}: OpcoRowProps): JSX.Element{
    // the key for default should not be editable.
    // this is only applicable to the key, as the default key cannot be edited but the value can.
    let inputEditable: boolean = isEditable && opco.opcoKey != DEFAULT_KEY ? false : true;

    const rowRef = useRef<HTMLTableRowElement|null>(null);

    // not really a fan of this but i spent too much time trying to figure out why
    // the opcoOptions update does not work in the parent component.
    useResetOpcoValues({
        baseOpco: baseOpco, 
        opco: opco, 
        resetProp: {resetDefault: defaultResetProp.resetDefault, setResetDefault: defaultResetProp.setResetDefault},
        rowRef: rowRef,
        setOpcoOptions: setOpcoOptions,
    });

    const keyIsLong: boolean = opco.opcoKey.length >= 16;
    const valueIsLong: boolean = opco.value.length >= 16;

    return (
        <>
            <tr
            ref={rowRef}>
                <td>
                    <input 
                    className="text-ellipsis"
                    type="text"
                    name="key"
                    readOnly={inputEditable}
                    title={
                        opco.opcoKey == DEFAULT_KEY && isEditable ? `Key ${opco.opcoKey} cannot be edited` 
                        : keyIsLong && !isEditable ? opco.opcoKey : ""
                    }
                    onChange={e => handleOpcoChange(e, opco, setOpcoOptions, "key")}
                    defaultValue={opco.opcoKey}/>
                </td>
                <td>
                    <input
                    type="text"
                    name="value"
                    readOnly={isEditable ? false : true}
                    title={valueIsLong && !isEditable ? opco.value : ""}
                    onChange={e => handleOpcoChange(e, opco, setOpcoOptions, "value")}
                    defaultValue={opco.value}/>
                </td>
                <td 
                className={`${isEditable && "hover:bg-gray-500"} flex justify-center items-center rounded-xl mr-1
                p-1`}
                onClick={() => { 
                    if(opco.opcoKey == DEFAULT_KEY){
                        toastError("Cannot delete default key");
                        return;
                    }
                    
                    if(isEditable){
                        removeOpco(opco, setOpcoOptions).then((status) => {
                            if(status){
                                partialResetProp.setStatus(true);
                            }
                        });
                    }
                }}>
                    <FaTrash color={!isEditable ? "gray" : "black"}/>
                </td>
            </tr>
        </>
    )
}

function handleOpcoChange(
    e: React.ChangeEvent<HTMLInputElement>,
    opco: OpcoRowProps["opco"],
    setOpcoOptions: OpcoRowProps["setOpcoOptions"],
    target: "key" | "value"){
        const newValue: string = e.currentTarget.value;

        setOpcoOptions(prev => 
            prev.map((prevOpco) => {
                if(opco.id != prevOpco.id){
                    return prevOpco;
                }

                if(target == "key"){
                    return {...prevOpco, opcoKey: newValue}
                }else{
                    return {...prevOpco, value: newValue}
                }
            })
        )
}

/**
 * Removes an operating company.
 * @param currID - 
 * @param setOpcoOptions - 
 */
async function removeOpco(
    opco: OpcoMap,
    setOpcoOptions: OpcoRowProps["setOpcoOptions"]): Promise<boolean>{
        const keyToRemove: string = opco.opcoKey;

        await window.pywebview.api.delete_opco_key(keyToRemove).then((res: Record<string, string>) => {
            if(!checkRes(res)){
                toastError(res["error"]);
                return false;
            }
        });

        setOpcoOptions((prev) => prev.filter(prevOpco => {
            return prevOpco.id != opco.id;
        }));

        return true;
}

type OpcoRowProps = {
    opco: OpcoMap,
    baseOpco: OpcoMap,
    defaultResetProp: {resetDefault: boolean, setResetDefault: React.Dispatch<React.SetStateAction<boolean>>},
    partialResetProp: {status: boolean, setStatus: React.Dispatch<React.SetStateAction<boolean>>},
    setOpcoOptions: React.Dispatch<React.SetStateAction<Array<OpcoMap>>>,
    setUpdateBaseRef: React.Dispatch<React.SetStateAction<boolean>>,
    isEditable: boolean,
}