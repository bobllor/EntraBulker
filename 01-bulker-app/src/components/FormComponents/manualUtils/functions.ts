import React from "react";
import { InputDataProps } from "./types";
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

export function handleDivClick(event: React.MouseEvent<HTMLDivElement, MouseEvent>, 
        selectedCell: string,
        setSelectedCell: React.Dispatch<React.SetStateAction<string>>): void{
    const element: HTMLElement = event.target as HTMLElement;

    if(selectedCell != '' && element.tagName != 'TD'){
        setSelectedCell('');
    }
}