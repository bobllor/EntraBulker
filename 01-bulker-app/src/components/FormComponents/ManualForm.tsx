import { useState, useRef, JSX } from "react";
import { validateInput } from "./manualUtils/functions";
import { formInputs } from "./manualUtils/vars";
import { useManualData } from "./manualUtils/hooks";
import { EditCellProps, FormStateProps, InputDataProps, ManualData, SelectStateProps } from "./manualUtils/types";
import ManualTable from "./ManualTable";
import { generateId, throttler } from "../../utils";
import Button from "../ui/Button";
import { toastError, toastResponse, toastSuccess } from "../../toastUtils";
import { Response } from "../../pywebviewTypes";

const submitFormThrottle = throttler((data: ManualData[], func: (...any: any) => any) => func(data));

/** Form for manual entries instead of reading an Excel file. */
export default function ManualForm({formState, selectState, editCellState}: ManualFormProps): JSX.Element{
    const divRef: React.RefObject<HTMLDivElement|null> = useRef(null);

    const [manualData, setManualData] = useManualData(formState);
    const [isProcessing, setIsProcessing] = useState(false);
    
    // input validation to prevent duplicates
    const [inputData, setInputData] = useState<InputDataProps>(
        {nameValue: '', opcoValue: ''}
    );

    const addEntry = async (): Promise<void> => {
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
                toastError('Empty entry in the name field is not allowed');
                return;
            }else if(nameInputValue == value){
                toastError('Cannot have duplicate values in the fields');
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
        
        const id: string = generateId();
        objTemp['id'] = id;

        console.info("Added new entry:", objTemp)
        setManualData(prev => [...prev, objTemp]);
    }

    const submitManualEntry = async(): Promise<void> => {
        if(manualData.length == 0){
            toastError("No entries found");
            return;
        }
        
        try{
            setIsProcessing(true);

            let res: Response = await window.pywebview.api.generate_manual_csv(manualData);
            
            toastResponse(res);
            if(res.status == 'success'){
                // allows navigation without modal popup
                formState.func(false);
            }
        }catch(e){
            console.error("Unexpected error occurred:", e);
        }finally{
            setIsProcessing(false);
        }
    }

    return (
        <>
            <div
            className="flex flex-col gap-3 pb-5"
            ref={divRef}>
                {formInputs.map((obj, i) => (
                    <div className="flex flex-col" 
                    key={i}>
                        <span className="p-1">
                            {obj.label}
                        </span>
                        <input name={Object.keys(inputData)[i]}
                        id={obj.name}
                        spellCheck={false}
                        className={`outline-blue-300 px-3 py-1 rounded-xl input-style`}
                        onChange={(e) => validateInput(e, setInputData)}
                        onKeyDown={(e) => e.key == 'Enter' && addEntry()}
                        type="text" />
                    </div>
                ))}
                <button
                className={`px-5 py-3 rounded-xl bg-blue-500 text-white hover:bg-blue-400`}
                onClick={() => addEntry()}>Add Entry</button>
            </div>
            <div
            className="relative overflow-y-scroll min-w-200 max-w-200 min-h-90 max-h-90 overflow-x-hidden">
                {manualData.length > 0 ? 
                <ManualTable manualData={manualData} setManualData={setManualData} select={selectState}
                 edit={editCellState}/> :
                <div
                className="w-full flex justify-center items-center bg-gray-200 px-4 py-1 uppercase">
                    <p><strong>No entries entered</strong></p>
                </div>
                }
            </div>
            <div>
                <Button type="submit" paddingX={10} paddingY={3}
                width={60} 
                func={() => submitFormThrottle(manualData, submitManualEntry)} 
                text={!isProcessing ? "Submit" : "⏳ Processing..."}/>
            </div>
        </>
    )
}

type ManualFormProps = {
    formState: FormStateProps,
    selectState: SelectStateProps,
    editCellState: EditCellProps,
}