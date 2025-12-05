import React, { JSX } from "react";
import { useContext, createContext, useState } from "react";
import { APISettings } from "../pywebviewTypes";
import { useInitSettings, useInitHeaders, useUpdateSettings, useUpdateHeaders } from "./hooks";
import { HeaderMap } from "../pywebviewTypes";

const SettingsContext = createContext<SettingsData>({
    apiSettings: {} as APISettings,
    setApiSettings: () => {},
    headers: {} as HeaderMap,
    setHeaders: () => {},
    updateSettings: false,
    setUpdateSettings: () => {},
    updateHeaders: false,
    setUpdateHeaders: () => {},
});

export const useSettingsContext = () => useContext(SettingsContext);

export function SettingsProvider({ children }: {children: JSX.Element}): JSX.Element {
    const [apiSettings, setApiSettings] = useState<APISettings>({} as APISettings);
    const [headers, setHeaders] = useState<HeaderMap>({} as HeaderMap);

    const [updateSettings, setUpdateSettings] = useState<boolean>(false);
    const [updateHeaders, setUpdateHeaders] = useState<boolean>(false);

    useInitSettings(setApiSettings);
    useInitHeaders(setHeaders);

    useUpdateSettings(updateSettings, setUpdateSettings, setApiSettings);
    useUpdateHeaders(updateHeaders, setUpdateHeaders, setHeaders);

    const data: SettingsData = {
        apiSettings,
        setApiSettings,
        headers,
        setHeaders,
        updateSettings,
        setUpdateSettings,
        updateHeaders,
        setUpdateHeaders
    }
    
    return (
        <>
            <SettingsContext.Provider value={data}>
                {children}
            </SettingsContext.Provider>
        </>
    )
}

export type SettingsData = {
    apiSettings: APISettings,
    setApiSettings: React.Dispatch<React.SetStateAction<APISettings>>,
    headers: HeaderMap,
    setHeaders: React.Dispatch<React.SetStateAction<HeaderMap>>,
    updateSettings: boolean,
    setUpdateSettings: React.Dispatch<React.SetStateAction<boolean>>,
    updateHeaders: boolean,
    setUpdateHeaders: React.Dispatch<React.SetStateAction<boolean>>,
}