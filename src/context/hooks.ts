import React, { useEffect } from "react"
import "../pywebview";
import { APISettings, Metadata } from "../pywebviewTypes";
import { HeaderData } from "./SettingsContext";
import { getMetadata, getReaderContent } from "../pywebviewFunctions";
import { ReaderType } from "../components/SettingsComponents/types";

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

export function useUpdateHeaders(updateHeaders: boolean, setUpdateHeaders: 
    Headers["setUpdateHeaders"], 
    setHeaders: Headers["setHeaders"]){
        useEffect(() => {
            if(updateHeaders){
                const readerType: ReaderType = "excel";

                getReaderContent(readerType).then((res) => {
                    setHeaders(res as HeaderData);
                })
                
                setUpdateHeaders(false);
            }
        }, [updateHeaders])
}

export function useInitMeta(setVersion: Meta["setVersion"]){
    useEffect(() => {
        getMetadata().then((meta) => {
            setVersion(meta.version);
        });
    }, [])
}

type SettingsProps = {
    setApiSettings: React.Dispatch<React.SetStateAction<APISettings>>,
    updateSettings: boolean,
    setUpdateSettings: React.Dispatch<React.SetStateAction<boolean>>,
}

type Headers = {
    headers: HeaderData,
    setHeaders: React.Dispatch<React.SetStateAction<HeaderData>>,
    updateHeaders: boolean,
    setUpdateHeaders: React.Dispatch<React.SetStateAction<boolean>>,
}

type Meta = {
    setVersion: React.Dispatch<React.SetStateAction<string>>,
}