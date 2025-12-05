import { checkRes, generateId } from "../../utils";
import { ReaderType, OpcoMap } from "./types";
import { toastError } from "../../toastUtils";
import React from "react";
import "../../pywebview";
import { SettingsData } from "../../context/SettingsContext";
import { updateSetting } from "../../pywebviewFunctions";
import { Response } from "../../pywebviewTypes";

/**
 * Handles text submission to update a key for the settings in the backend.
 * @param event - The React form event.
 * @param readerType - The type to obtain the correct value from the target Reader in the backend.
 */
export async function updateExcelReader(keyName: string, value: string, readerType: ReaderType): Promise<boolean>{
    await window.pywebview.api.update_key(readerType, keyName, value).then((res: Response) => {
        if(!checkRes(res)){
            toastError(res["message"]);
            return false;
        } 
    });

    return true;
}

/**
 * Adds an entry into the operating company map. It updates the front end state and the back end config.
 * @param event - The form event of the inputs.
 * @param setOpcoOptions - The state function to add a new entry in the OpcoMap array.
 * @returns {Promise<boolean>}
 */
export async function addOpcoEntry(
    event: React.FormEvent<HTMLFormElement>, 
    setOpcoOptions: React.Dispatch<React.SetStateAction<Array<OpcoMap>>>): Promise<boolean>{
        event.preventDefault();
        // NOTE: div exists over the input elements.
        const children = event.currentTarget.children[0].children;

        // keys of inputData object
        const keyName = "keyOpco";
        const valueName = "valueOpco";

        const opcoHolder: OpcoMap = {opcoKey: "", value: "", id: generateId()};

        // NOTE: FormData does this better. future me please!
        for(let i = 0; i < children.length; i++){
            const element: HTMLInputElement = children[i] as HTMLInputElement;

            if(element.tagName != "INPUT"){
                continue;
            }

            if(element.getAttribute("type") == "submit"){
                continue;
            }

            // validation will not allow this to be empty.
            const value: string = element.value;
            const elementName: string = element.getAttribute("name")!;

            if(elementName == keyName){
                opcoHolder.opcoKey = value.toLowerCase();
                element.focus();
            }else if(elementName == valueName){
                opcoHolder.value = value;
            }

            element.value = "";
        }

        setOpcoOptions(prev => [...prev, opcoHolder]);

        await window.pywebview.api.add_opco(opcoHolder).then((res: Record<string, string>) => {
            if(!checkRes(res)){
                toastError(res["message"]);
                return false;
            };
        });

        return true;
}

/**
 * Sets the output directory of a chosen directory
 * @param setApiSettings State setter function for the API settings of the program
 */
export async function setOutputDir(setApiSettings: SettingsData["setApiSettings"]): Promise<void>{
    await window.pywebview.api.set_output_dir().then((res: Record<string, string>) => {
        if(res["status"] == "success"){
            setApiSettings(prev => ({...prev, output_dir: res["content"]}));
        }
    });
}

/**
 * Enables/disables the text generation when generating the CSV file
 * @param state The given state to set the setting
 * @param setApiSettings State setter function for the API settings of the program
 */
export async function setTextGenerationState(state: boolean, setApiSettings: SettingsData["setApiSettings"]): Promise<void>{
    // these values must match the types shown in both the back end and front end types (and the config).
    const key: string = "enabled";
    const parentKey: string = "template";

    // state must be inverted, as the value will not update properly.
    // for example: it starts false, but will pass in false. it is inverted to pass true to update.
    await window.pywebview.api.update_setting(key, !state, parentKey).then((res: Record<string, string>) => {
        // errors dont need to be handled. if there is one it has bigger issues.
        if(res["status"] == "success"){
            setApiSettings(prev => ({...prev, template: {...prev.template, enabled: !prev.template.enabled}}));
        }
    })
}

export async function setSetting(key: string, state: any, func: (...any: any[]) => void, 
    parent: string | undefined = undefined): Promise<void>{
    updateSetting(key, state, parent).then((res) => {
        if(res.status == "error"){
            toastError(res.message);
            return;
        }

        func();
    });
}

/**
 * Updates the Formatting map of the settings configuration
 * @param key The target key to be changed
 * @param value The new value of the target key
 * @param setApiSettings The state setter function for updating the settings state
 */
export async function updateFormattingKey(
    key: string, value: any, setApiSettings: SettingsData["setApiSettings"]): Promise<void>{
        await window.pywebview.api.update_setting(key, value, "format").then((res: Record<string, string>) => {
            if(res["status"] == "success"){
                setApiSettings(prev => (
                    {...prev, format: {...prev.format, [key]: value}}
                ))
            }
        });
}