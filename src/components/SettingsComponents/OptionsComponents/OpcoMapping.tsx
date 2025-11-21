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
import Button from "../../ui/Button";
import { ToolTip } from "../../ui/ToolTip";

const title: string = "Operating Company";
const tooltipText: string = "Mapping of operating company to a domain name.";
const inputLabel: InputLabelProps = {keyOpco: "Operating Company", valueOpco: "Domain"};

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
                    className="p-2 h-fit"
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
                                        setInputData(prev => ({...prev, keyOpco: "", valueOpco: ""}));
                                    }
                                });
                            }
                        }>
                        {/* The opco submission entry */}
                        <div
                        className="flex flex-col justify-center items-center gap-1">
                            {Object.keys(inputData).map((name, i) => (
                                <React.Fragment
                                key={name}>
                                    <label
                                    htmlFor={name}
                                    className="capitalize">
                                        {inputLabel[name as keyof InputLabelProps]}:
                                    </label>
                                    <input 
                                    className="border-1 outline-0 rounded-xl py-1 px-2 w-[30%]"
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
                                </React.Fragment>
                            ))}
                            <Button text="Submit" type="submit" paddingX={5}/>
                        </div>
                    </form>
                    <div className="flex gap-1">
                        {/* Table editing logic */}
                        <div className="p-1 w-20 ml-1 hover:bg-gray-500 flex items-center justify-center
                        rounded-tl-xl rounded-tr-xl border-l-1 border-r-1 border-t-1"
                        title={!isEditable ? "Edit table" : "Confirm"}
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
                            className="flex items-center justify-center hover:bg-gray-500 w-20
                            rounded-tl-xl rounded-tr-xl border-l-1 border-r-1 border-t-1"
                            title="Cancel">
                                <FaTimes color="red" />
                            </div>
                        }
                    </div>
                    {/* The table */}
                    <table className="w-full text-center table-fixed mb-30">
                        <thead className="border-t-1 border-b-1">
                            <tr>
                                <th>Operating Company</th>
                                <th>Domain</th>
                                <th className="w-10">
                                    <div className="flex justify-center items-center">
                                        <ToolTip text="To modify rows, enter edit mode." />
                                    </div>
                                </th>
                            </tr>
                        </thead>
                        <tbody className="">
                            {opcoOptions.map((opco, i) => (
                                <React.Fragment
                                key={opco.id}>
                                    <OpcoRow opco={opco} 
                                    defaultResetProp={{resetDefault: resetDefault, setResetDefault: setResetDefault}}
                                    isEditable={isEditable} setOpcoOptions={setOpcoOptions}
                                    partialResetProp={{status: partialUpdate, setStatus: setPartialUpdate}}
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

type InputLabelProps = {
    keyOpco: string, 
    valueOpco: string,
};