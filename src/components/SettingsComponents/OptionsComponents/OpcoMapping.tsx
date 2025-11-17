import React, { JSX, useState, useRef } from "react";
import { OpcoMap, ReaderType } from "../types";
import { useOpcoInit, useUpdateBaseSetOpco } from "../hooks";
import { addOpcoEntry } from "../functions";
import { compareObjects } from "../../../utils";
import OptionBase from "./OptionBase";
import OpcoRow from "./OpcoRow";
import { toastError } from "../../../toastUtils";
import "../../../pywebview";
import { FaCheck, FaEdit, FaTimes } from "react-icons/fa";

const title: string = "Operating Company";
const tooltipText: string = "Mapping of operating company to a domain name.";

export default function OpcoMapping(): JSX.Element{
    const [opcoOptions, setOpcoOptions] = useState<Array<OpcoMap>>([]);
    const [inputData, setInputData] = useState({keyOpco: "", valueOpco: ""});
    const [isEditable, setIsEditable] = useState(false);

    const [updateBaseRef, setUpdateBaseRef] = useState<boolean>(false);
    const [partialUpdate, setPartialUpdate] = useState<boolean>(false);

    // used to reset the data to default values.
    const [resetDefault, setResetDefault] = useState<boolean>(false);

    // used to keep track of the previous options prior to any updates.
    const baseOpcoRef = useRef<Array<OpcoMap>>([]);
    const opcoKeysRef = useRef<Set<string>>(new Set());

    useOpcoInit(baseOpcoRef, opcoKeysRef, setOpcoOptions);

    useUpdateBaseSetOpco({context: {
        fullUpdate: {status: updateBaseRef, setStatus: setUpdateBaseRef},
        partialUpdate: {status: partialUpdate, setStatus: setPartialUpdate},
        opcoOptions: opcoOptions,
        baseOpcoRef: baseOpcoRef,
        opcoKeysRef: opcoKeysRef,
    }});

    return (
        <>
            <OptionBase title={title} tooltipText={tooltipText} element={
                opcoOptions.length == 0 
                ? 
                <div>
                    {/* one entry will always exist, it is only empty on initial load */}
                    TODO: add the spinner here
                </div>
                : <>
                    <form
                    className="p-2"
                    onSubmit={e => {
                                e.preventDefault();
                                // update the base ref after calling this.
                                if(opcoKeysRef.current.has(inputData.keyOpco)){
                                    toastError(`Key ${inputData.keyOpco} already exists`);
                                    return;
                                }else if(inputData.keyOpco.trim() == ""){
                                    toastError(`Key cannot be empty`);
                                    return;
                                }

                                addOpcoEntry(e, setOpcoOptions).then((status) => {
                                    if(status){
                                        setUpdateBaseRef(true);
                                    }
                                });
                            }
                        }>
                        {/* The opco submission entry */}
                        {Object.keys(inputData).map((name, i) => (
                            <input 
                            key={i}
                            type="text"
                            onChange={e => {
                                const input: HTMLInputElement = e.currentTarget;
                                const value: string = input.value.toLowerCase();

                                setInputData(prev => {
                                    if(input.getAttribute("name")!.includes("key")){
                                        return {...prev, keyOpco: value};
                                    }

                                    return {...prev, valueOpco: value};
                                })
                            }}
                            name={name} />
                        ))}
                        <input type="submit"/>
                    </form>
                    <div className="flex">
                        {/* Table editing logic */}
                        <div className="p-1 w-20 hover:bg-gray-500 flex items-center justify-center"
                        title={!isEditable ? "Edit table" : "Confirm changes"}
                        onClick={() => {
                                if(isEditable){
                                    updateOpcoMapping(opcoOptions, baseOpcoRef).then(status => {
                                        if(status){
                                            setUpdateBaseRef(true);
                                        }
                                    });
                                }
                                setIsEditable(prev => !prev);
                            }
                        }>
                            {!isEditable ? <FaEdit color="#286db2" /> : <FaCheck color="green" />}
                        </div>
                        {isEditable && 
                            <div 
                            onClick={() => {
                                // this is manually edited inside OpcoRow, i cannot figure out
                                // why setOpcoOptions does not get updated.
                                // something with baseOpcoRef.current... i dont know.
                                setIsEditable(prev => !prev);
                                setResetDefault(true);
                            }}
                            className="flex items-center justify-center hover:bg-gray-500 w-20"
                            title="Cancel">
                                <FaTimes color="red" />
                            </div>
                        }
                    </div>
                    {/* The table */}
                    <table className="w-full text-center border-1 table-fixed">
                        <thead>
                            <tr>
                                <th>Operating Company</th>
                                <th>Domain</th>
                                <th className="w-10">{/*empty element, used for Trash in OpcoRow */}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {opcoOptions.map((opco, i) => (
                                <React.Fragment
                                key={opco.id}>
                                    <OpcoRow opco={opco} 
                                    defaultResetProp={{resetDefault: resetDefault, setResetDefault: setResetDefault}}
                                    isEditable={isEditable} setOpcoOptions={setOpcoOptions}
                                    partialResetProp={{status: partialUpdate, setStatus: setPartialUpdate}}
                                    setUpdateBaseRef={setUpdateBaseRef}
                                    baseOpco={baseOpcoRef.current[i]}/>
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </>
            }/>
        </>
    )
}

/**
 * Updates the operating company mapping for the backend. The operating company array mapper is updated inside
 * `OpcoRow`.
 * @param opcoOptions - The operating company array mapper.
 * @param baseOpcoRef - The base operating company array mapper, used to prevent calls on unchanged values.
 * @returns funcStatus - If the function succeeds or not.
 */
async function updateOpcoMapping(
    opcoOptions: Array<OpcoMap>,
    baseOpcoRef: React.RefObject<Array<OpcoMap>>): Promise<boolean>{
        let hasChanged: boolean = false;
        for (let i = 0; i < baseOpcoRef.current.length; i++) {
            if(hasChanged){
                break;
            }

            const baseOpco: OpcoMap = baseOpcoRef.current[i];
            const newOpco: OpcoMap = opcoOptions[i]; 

            hasChanged = compareObjects(baseOpco, newOpco);
        }

        if(hasChanged){
            let flattenedOpcoMap: Record<string, string> = {};
            // flattening the opco for the backend call
            opcoOptions.forEach((opco) => {
                const newKey: string = opco.opcoKey.toLowerCase();
                const newVal: string = opco.value.toLowerCase();

                flattenedOpcoMap[newKey] = newVal;
            })
            
            const reader: ReaderType = "opco";

            await window.pywebview.api.insert_update_rm_many(reader, flattenedOpcoMap).then((res: Record<string, string>) => {
                if(res["status"] != "success"){
                    toastError(res["message"]);
                }                
            });

            // update the base ref.
            baseOpcoRef.current = [...opcoOptions];
        }

        return hasChanged;
}