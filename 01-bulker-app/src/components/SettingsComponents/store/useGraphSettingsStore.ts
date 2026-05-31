import {create} from "zustand";
import "../../../pywebview";
import { getReaderContent } from "../../../pywebviewFunctions";

type GraphSettingStore = {
    values: GraphSettingValues
    /**
     * Initializes the data from the backend call.
     * @returns 
     */
    initialize: () => Promise<void>
}

type GraphUserType = "Member" | "Guest";

type GraphSettingValues = {
    client_id: string
    tenant_id: string
    enable_graph: boolean
    user_type:  GraphUserType
}

export const useGraphSettingStore = create<GraphSettingStore>(set => ({
    values: {
        client_id: "",
        tenant_id: "",
        enable_graph: false,
        user_type: "Guest",
    },
    initialize: async () => {
        const graphSettings = await getReaderContent("graph") as GraphSettingValues;

        set(prev => ({...prev, values: graphSettings}));
    }
}));