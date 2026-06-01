import {create} from "zustand";
import "../../../pywebview";
import { getReaderContent, updateReader } from "../../../pywebviewFunctions";
import { toastResponse } from "../../../toastUtils";

type GraphSettingStore = {
    values: GraphSettingValues
    /**
     * Initializes the data from the backend call.
     * @returns 
     */
    initialize: () => Promise<void>
    /**
     * Updates the Graph values based on the key and the given value.
     * This will update the context and the backend server.
     * 
     * @param key The key to update
     * @param value The value used for the key
     * @returns 
     */
    setGraphValues: (key: string, value: any) => Promise<void>
}

type GraphUserType = "member" | "guest";

type GraphSettingValues = {
    client_id: string
    tenant_id: string
    enable_graph: boolean
    member_type_domain_csv: string
    user_type:  GraphUserType
}

export const useGraphSettingStore = create<GraphSettingStore>(set => ({
    values: {
        client_id: "",
        tenant_id: "",
        enable_graph: false,
        member_type_domain_csv: "",
        user_type: "guest",
    },
    initialize: async () => {
        const graphSettings = await getReaderContent("graph") as GraphSettingValues;

        set(prev => ({...prev, values: graphSettings}));
    },
    setGraphValues: async (key: string, value: any) => {
        await updateReader("graph", key, value);

        set(prev => ({...prev, values: {...prev.values, [key]: value}}));
    },
}));