import { create } from "zustand";
import { GraphError, Response } from "../../../pywebviewTypes";

type ProcessingErrorStore = {
    errors: Array<ProcessingErrorObject>
    /**
     * Fetches a graph error to the error object of the store. If the return from
     * the content of API call is undefined, then it will do nothing.
     * This must be called after the CSV has been generated.
     * 
     * @param fileName The file that failed
     * @returns 
     */
    fetchGraphError: (fileName: string) => Promise<void>,
}

export type ProcessingErrorObject = {
    fileName: string
    id: string
    graphError: GraphError
}

export const useProcessingErrorStore = create<ProcessingErrorStore>((set, get) => ({
    errors: [],
    fetchGraphError: async (fileName: string) => {
        const res: Response = await window.pywebview.api.get_user_graph_errors();
        const graphError: GraphError | undefined = res["content"]

        console.log(res);
        if(graphError !== undefined){
            let uuid = crypto.randomUUID();
            const obj: ProcessingErrorObject = {
                fileName: fileName,
                id: uuid,
                graphError: graphError,
            };

            set(st => ({...st, errors: [...st.errors, obj]}));
        }
    },
}));