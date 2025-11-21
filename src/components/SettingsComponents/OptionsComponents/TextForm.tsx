import { JSX, useState } from "react";
import OptionBase from "./OptionBase";
import Button from "../../ui/Button";
import { SettingsData, useSettingsContext } from "../../../context/SettingsContext";
import { updateSetting } from "../../../pywebviewFunctions";
import { toastError } from "../../../toastUtils";

const title: string = "Text Template";
const tooltipText: string = "Settings for the text output for each row.";
const maxTextLength: number = 1250;

export default function TextForm(): JSX.Element{
    return (
        <>
            <OptionBase title={title} tooltipText={tooltipText} 
            element={<TextField />}/>
        </>
    )
}

function TextField(): JSX.Element{
    const {apiSettings, setApiSettings} = useSettingsContext();

    const [textValue, setTextValue] = useState<string>(apiSettings.template.text);

    return (
        <>
            <form
            className="p-2"
            onSubmit={e => {
                    e.preventDefault();

                    textSubmission(textValue, setApiSettings);
                }}>
                <div className="flex flex-col items-center justify-center gap-2">
                    <textarea
                    maxLength={maxTextLength}
                    onChange={(e) => {
                        const value: string = e.currentTarget.value;

                        setTextValue(value);
                    }}
                    value={textValue} 
                    className="relative bg-white resize-none rounded-xl border-1 p-2 w-[90%] h-60 outline-none">
                    </textarea>
                    <span className={`${textValue.length >= maxTextLength && "text-red-500"}`}>
                        {textValue.length}/{maxTextLength}
                    </span>
                    <Button text="Submit" type="submit"/>
                </div>
            </form>
        </>
    )
}

async function textSubmission(text: string, setApiSettings: SettingsData["setApiSettings"]): Promise<void>{
    const res = await updateSetting("text", text, "template");

    if(res.status == "success"){
        setApiSettings(prev => ({...prev, template: {...prev.template, text: text}}));
    }else{
        toastError(res.message);
    }
}