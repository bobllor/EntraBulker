import React, { useEffect } from "react";
import { OpcoMap, ReaderType } from "./types";
import { generateId } from "../../utils";
import "../../pywebview";

/**
 * Hook used to initialize the operating company mapping from the backend.
 * @param baseOpcoRef - A RefObject used to store the base values of `opcoOptions` from the call.
 * @param opcoKeysRef - The hash set of operating company keys, it is filled in the call.
 * @param setOpcoFunc - The React dispatch function for the operating company state.
 */
export function useOpcoInit(
    baseOpcoRef: React.RefObject<Array<OpcoMap>>,
    opcoKeysRef: React.RefObject<Set<string>>,
    setOpcoFunc: React.Dispatch<React.SetStateAction<Array<OpcoMap>>>,
    ){
        const setReaderContent = async (reader: ReaderType) => {
        await window.pywebview.api.get_reader_content(reader).then((res: Record<string, string>) => {
            const keys: Array<string> = Object.keys(res)

            const opcos: Array<OpcoMap> = [];
            keys.forEach(key => {
                const opco: OpcoMap = Object();

                opco.opcoKey = key.toLowerCase();
                // domain will not be lowercase.
                opco.value = res[key];
                opco.id = generateId();

                opcos.push(opco);
                opcoKeysRef.current.add(opco.opcoKey);
                baseOpcoRef.current.push(opco);
            })

            setOpcoFunc(prev => [...prev, ...opcos]);
        })
        }

        const reader: ReaderType = "opco";

        useEffect(() => {
            setReaderContent(reader);
        }, [])
}

/**
 * Hook for updating the base operating company reference for holding the previous state and the keys set.
 * It updates based off of two conditions: 
 * 1. fullUpdate: Modifies the entire reference and its values, it is mutated and updated to match the current state.
 * 2. partialUpdate: Does not modify the reference and its values, instead it drops missing objects based on the current state.
 * This is only relevant during deletion.
 * @param context - The UpdateBaseProps context for the hook.
 */
export function useUpdateBaseSetOpco({context}: {context: UpdateBaseProps}){
    useEffect(() => {
        if(context.fullUpdate.status){
            context.baseOpcoRef.current = [...context.opcoOptions];

            context.opcoKeysRef.current.clear() 
            context.opcoKeysRef.current = new Set(context.opcoOptions.map((opco) => opco.opcoKey));

            context.fullUpdate.setStatus(false);
        }else if(context.partialUpdate.status){
            // the data is not replaced, but instead the data is dropped.
            // this is due to modifications that occur during the editing state.
            const newIds: Set<string> = new Set([...context.opcoOptions.map((opco) => opco.id)]);
            const filteredBaseOpcos: Array<OpcoMap> = context.baseOpcoRef.current.filter((opco) => newIds.has(opco.id))
            
            context.baseOpcoRef.current = [...filteredBaseOpcos];
            context.opcoKeysRef.current.clear() 
            context.opcoKeysRef.current = new Set(filteredBaseOpcos.map((opco) => opco.opcoKey));
        
            context.partialUpdate.setStatus(false);
        }
    }, [context.fullUpdate.status, context.partialUpdate.status])
}

/**
 * Hook for resetting the values of the table data input elements for modifying data.
 * @param context - ResetOpcoValuesProp for setting up the hook.
 */
export function useResetOpcoValues(context: ResetOpcoValuesProp){
    useEffect(() => {
        if(context.resetProp.resetDefault){
            const trChildren = context.rowRef.current!.children; 

            for(let i = 0; i < trChildren.length; i++){
                const td = trChildren[i] as HTMLTableCellElement;

                const inputEle = td.children[0] as HTMLInputElement;

                const inputType = inputEle.getAttribute("name");
                
                if(inputType == "key"){
                    inputEle.value = context.baseOpco.opcoKey;
                }else if(inputType == "value"){
                    inputEle.value = context.baseOpco.value;
                }
            }

            context.setOpcoOptions(prev => {
                return prev.map(prevOpco => {
                    if(context.opco.id == prevOpco.id){
                        return {...prevOpco, opcoKey: context.baseOpco.opcoKey, value: context.baseOpco.value};
                    }

                    return prevOpco;
                })
            });
        }

        context.resetProp.setResetDefault(false);
    }, [context.resetProp.resetDefault])
}

type UpdateBaseProps = {
    fullUpdate: {status: boolean, setStatus: React.Dispatch<React.SetStateAction<boolean>>},
    partialUpdate: {status: boolean, setStatus: React.Dispatch<React.SetStateAction<boolean>>},
    opcoOptions: Array<OpcoMap>,
    baseOpcoRef: React.RefObject<Array<OpcoMap>>,
    opcoKeysRef: React.RefObject<Set<string>>,
}

type ResetOpcoValuesProp = {
    resetProp: {resetDefault: boolean, setResetDefault: React.Dispatch<React.SetStateAction<boolean>>},
    rowRef: React.RefObject<HTMLTableRowElement|null>,
    setOpcoOptions: React.Dispatch<React.SetStateAction<Array<OpcoMap>>>,
    opco: OpcoMap,
    baseOpco: OpcoMap,
}