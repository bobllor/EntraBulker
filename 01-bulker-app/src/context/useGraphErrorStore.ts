import { create } from "zustand";
import { GraphError, Response } from "../pywebviewTypes";
import "../pywebview";

type GraphErrorStore = {
    errors: Array<GraphErrorObject>
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

export type GraphErrorObject = {
    fileName: string
    id: string
    graphError: GraphError
}

export const useGraphErrorStore = create<GraphErrorStore>((set, get) => ({
    errors: [],
    fetchGraphError: async (fileName: string) => {
        const res: Response = await window.pywebview.api.get_user_graph_errors();
        const graphError: GraphError | undefined = res["content"]

        console.log(res);
        if(graphError !== null && graphError !== undefined){
            let uuid = crypto.randomUUID();
            const obj: GraphErrorObject = {
                fileName: fileName,
                id: uuid,
                graphError: graphError,
            };

            set(st => ({...st, errors: [...st.errors, obj]}));
        }
    },
}));