import { useState, useEffect } from "react";
import { FormStateProps, ManualData } from "./types";

//** An array of objects that represent the manual input of the form. */
export function useManualData(formState: FormStateProps): readonly 
        [ManualData[], React.Dispatch<React.SetStateAction<ManualData[]>>]{
    const [manualData, setManualData] = useState<Array<ManualData>>([]);

    useEffect(() => {
        if(manualData.length == 0){
            formState.func(false);
        }else{
            formState.func(true);
        }
    }, [manualData])

    return [manualData, setManualData] as const;
}