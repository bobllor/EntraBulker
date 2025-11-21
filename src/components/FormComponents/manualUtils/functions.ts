import React, { Dispatch } from "react";
import { InputDataProps } from "./types";
import { ManualData } from "./types";
import { formInputs } from "./vars";
import { toaster } from "../../../toastUtils";
import "../../../pywebview";

export async function addEntry(
    divRef: React.RefObject<HTMLDivElement|null>,
    setData: Dispatch<React.SetStateAction<ManualData[]>>): Promise<void>{
    if(!divRef.current) return;

    const objTemp: ManualData = {};

    const objProps: Array<string> = ['name', 'opco'];

    // used to prevent the name and opco fields from being the same value.
    let nameInput: null|HTMLInputElement = null;
    let nameInputValue: null|string = null;
    
    // not sure if there is a better way to do this, i tried thinking about using refs in ManualForm but
    // it wouldn't work really well because of the loop to create the elements
    const inputElements: NodeListOf<HTMLInputElement> = divRef.current!.querySelectorAll('input');
    let index: number = 0;

    for(const input of inputElements){
        const value: string = input.value.trim();

        if(value == '' && input.id.includes('name')){
            toaster('Empty entry in the name field is not allowed.', "error");
            return;
        }else if(nameInputValue == value){
            toaster('Cannot have duplicate values in the fields.', "error");
            return;
        }

        if(!nameInput && !nameInputValue){
            nameInput = input;
            nameInputValue = input.value;
        }

        if(formInputs[index].name == input.id){
            objTemp[objProps[index] as keyof ManualData] = input.value;
        }

        index += 1;
    }

    // only resets the values if successful
    for(const input of inputElements){
        input.value = '';
    }

    nameInput?.focus();
    
    const id: string = Date.now().toString();
    objTemp['id'] = id;

    setData(prev => [...prev, objTemp]);
}

/**
 * Validates the form inputs to ensure no duplicates are in either field, if it fails then
 * the input field is highlighted red and the button is disabled. This only handles two input elements.
 * @param event The HTML input element 
 * @param setInputData The react dispatch of the input data state.
 * @param setDisableSubmit The react dispatch to disable the submit button 
 */
export function validateInput(event: React.ChangeEvent<HTMLInputElement>,
    setInputData: React.Dispatch<React.SetStateAction<InputDataProps>>, 
    setDisableSubmit: React.Dispatch<React.SetStateAction<boolean>>){
        const elementName: string = event.currentTarget.name;
        const currValue: string = event.currentTarget.value;

        setInputData(prev => {
            // retrieves the opposite input key from the current one
            const otherKey: string = Object.keys(prev).filter((key) => key != elementName)[0];
            const otherVal: string = prev[otherKey as keyof InputDataProps];
            
            if(otherVal == currValue && otherVal != '' && currValue != ''){
                setDisableSubmit(true);
            }else{
                setDisableSubmit(false);
            }

            return {...prev, [elementName]: currValue}
        })
}

export async function submitManualEntry(manualData: Array<ManualData>): Promise<void>{
    if(manualData.length == 0){
        toaster('No entries found.', "error");
        return;
    }

    let res: {status: string, message: string} = await window.pywebview.api.generate_manual_csv(manualData);

    if(res.status == 'success'){
        toaster(res.message, "success");
    }
}

export function handleDivClick(event: React.MouseEvent<HTMLDivElement, MouseEvent>, 
        selectedCell: string,
        setSelectedCell: React.Dispatch<React.SetStateAction<string>>): void{
    const element: HTMLElement = event.target as HTMLElement;

    if(selectedCell != '' && element.tagName != 'TD'){
        setSelectedCell('');
    }
}