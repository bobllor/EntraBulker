import React, { useEffect } from "react"
import "../pywebview";
import { APISettings, HeaderMap } from "../pywebviewTypes";
import { getMetadata, getReaderContent } from "../pywebviewFunctions";
import { ReaderType } from "../components/SettingsComponents/types";


const timeout: number = 600;
/**
 * Initializes the settings context
 * @param setApiSettings State setter function for initializing the settings of the program.
 */
export function useInitSettings(setApiSettings: SettingsProps["setApiSettings"]){
    useEffect(() => {
        setTimeout(() => {
            getReaderContent("settings").then((res) => {
                setApiSettings(res as APISettings);
            })
        }, timeout);
    }, [])
}

/**
 * Initializes the headers context
 * @param setHeaders State setter function for setting Headers
 */
export function useInitHeaders(setHeaders: Headers["setHeaders"]){
    useEffect(() => {
        setTimeout(() => {
            getReaderContent("excel").then((res) => {
                setHeaders(res as HeaderMap);
            })
        }, timeout);
    }, [])
}

/**
 * Initializes the meta data context
 * @param setVersion The setter function for the version state
 */
export function useInitMeta(setVersion: Meta["setVersion"]){
    useEffect(() => {
        setTimeout(() => 
            getMetadata().then((meta) => setVersion(meta.version))
        , timeout);
    }, [])
}

/**
 * Hook to update the API settings when an update event occurs
 * @param updateSettings The update state
 * @param setUpdateSettings The update setter function to reset the state
 * @param setApiSettings The API settings setter function
 */
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

/**
 * Side effect to update headers
 * @param updateHeaders The effect used as the dependency
 * @param setUpdateHeaders Setter function of the state to reset the effect
 * @param setHeaders The Headers setter function to update
 */
export function useUpdateHeaders(updateHeaders: boolean, setUpdateHeaders: 
    Headers["setUpdateHeaders"], 
    setHeaders: Headers["setHeaders"]){
        useEffect(() => {
            if(updateHeaders){
                const readerType: ReaderType = "excel";

                getReaderContent(readerType).then((res) => {
                    setHeaders(res as HeaderMap);
                })
                
                setUpdateHeaders(false);
            }
        }, [updateHeaders])
}

type SettingsProps = {
    setApiSettings: React.Dispatch<React.SetStateAction<APISettings>>,
    updateSettings: boolean,
    setUpdateSettings: React.Dispatch<React.SetStateAction<boolean>>,
}

type Headers = {
    headers: HeaderMap,
    setHeaders: React.Dispatch<React.SetStateAction<HeaderMap>>,
    updateHeaders: boolean,
    setUpdateHeaders: React.Dispatch<React.SetStateAction<boolean>>,
}

type Meta = {
    setVersion: React.Dispatch<React.SetStateAction<string>>,
}