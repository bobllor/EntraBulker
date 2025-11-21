import React, { useEffect } from "react"
import "../pywebview";
import { APISettings } from "../pywebviewTypes";
import { HeaderData } from "./SettingsContext";
import { getReaderContent } from "../pywebviewFunctions";

/**
 * Hook to initialize the settings context.
 * @param setApiSettings State setter function for initializing the settings of the program.
 */
export function useInitSettings(setApiSettings: SettingsProps["setApiSettings"]){
    useEffect(() => {
        getReaderContent("settings").then((res) => {
            setApiSettings(res as APISettings);
        })
    }, [])
}

/**
 * Hook to initialize the headers context
 * @param setHeaders State setter function for setting Headers
 */
export function useInitHeaders(setHeaders: Headers["setHeaders"]){
    useEffect(() => {
        getReaderContent("excel").then((res) => {
            setHeaders(res as HeaderData);
        })
    }, [])
}

export function useUpdateSettings(
    updateSettings: boolean, 
    setUpdateSettings: SettingsProps["setUpdateSettings"],
    setApiSettings: SettingsProps["setApiSettings"]){
        useEffect(() => {
            if(updateSettings){
                getReaderContent("settings").then((res) => {
                    setApiSettings(res as APISettings);

                    setUpdateSettings(false);
                })
            }
        }, [updateSettings])
}

type SettingsProps = {
    setApiSettings: React.Dispatch<React.SetStateAction<APISettings>>,
    updateSettings: boolean,
    setUpdateSettings: React.Dispatch<React.SetStateAction<boolean>>,
}

type Headers = {
    setHeaders: React.Dispatch<React.SetStateAction<HeaderData>>,
}