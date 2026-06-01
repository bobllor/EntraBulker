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
     * Uses the current status of the enable graph status and inverses it
     * to update the option.
     * 
     * @param status The current status of the enable graph status 
     * @returns 
     */
    updateEnableGraphStatus: (status: boolean) => Promise<void>
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
    },
    updateEnableGraphStatus: async (status: boolean) => {
        await updateReader("graph", "enable_graph", !status);

        set(prev => ({...prev, values: {...prev.values, enable_graph: !status}}));
    } 
}));