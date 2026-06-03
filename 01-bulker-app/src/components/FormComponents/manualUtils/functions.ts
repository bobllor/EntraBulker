import React from "react";
import { InputDataProps } from "./types";
import { ManualData } from "./types";
import { toastError, toastSuccess } from "../../../toastUtils";
import "../../../pywebview";

/**
 * Validates the form inputs to ensure no duplicates are in either field, if it fails then
 * the input field is highlighted red and the button is disabled. This only handles two input elements.
 * @param event The HTML input element 
 * @param setInputData The react dispatch of the input data state.
 * @param setDisableSubmit The react dispatch to disable the submit button 
 */
export function validateInput(event: React.ChangeEvent<HTMLInputElement>,
    setInputData: React.Dispatch<React.SetStateAction<InputDataProps>>){
        const elementName: string = event.currentTarget.name;
        const currValue: string = event.currentTarget.value;

        setInputData(prev => {
            return {...prev, [elementName]: currValue}
        })
}

export async function submitManualEntry(manualData: Array<ManualData>): Promise<void>{
    if(manualData.length == 0){
        toastError("No entries found");
        return;
    }

    let res: {status: string, message: string} = await window.pywebview.api.generate_manual_csv(manualData);

    if(res.status == 'success'){
        toastSuccess(res.message);
    }else{
        toastError(res.message);
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