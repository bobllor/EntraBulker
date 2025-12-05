import { JSX, useState } from "react";
import OptionBase from "./OptionBase";
import Button from "../../ui/Button";
import { SettingsData, useSettingsContext } from "../../../context/SettingsContext";
import { updateSetting } from "../../../pywebviewFunctions";
import { toastError, toastSuccess } from "../../../toastUtils";
import { ToolTip } from "../../ui/ToolTip";
import { FaAngleDown, FaAngleRight } from "react-icons/fa";
import { throttler } from "../../../utils";

const title: string = "Text Template";
const tooltipText: string = "Generating the text template containing the login for the user";
const maxTextLength: number = 1250;

export default function TextForm(): JSX.Element{
    return (
        <>
            <OptionBase title={title} tooltipText={tooltipText} 
            element={<TextField />}/>
        </>
    )
}

const throttle = throttler(
    (textValue: string, updaterFunc: (...args:any) => any) => textSubmission(textValue, updaterFunc)
);

function TextField(): JSX.Element{
    const {apiSettings, setApiSettings} = useSettingsContext();

    const [textValue, setTextValue] = useState<string>(apiSettings.template.text);
    const [showHelp, setShowHelp] = useState<boolean>(false);

    return (
        <>
            <div className="w-full flex flex-col items-center px-5">
                <div className="w-full">
                    <div 
                    onClick={() => setShowHelp(prev => !prev)}
                    className="relative flex justify-start items-center gap-1 hover:bg-gray-400 min-w-32 max-w-32 px-2 rounded-xl">
                        {!showHelp ? <FaAngleRight /> : <FaAngleDown />}
                        <span>
                            How to use
                        </span>
                    </div>
                    {showHelp && <HowToUseText />}
                </div>
            </div>
            <form
            className="p-2"
            onSubmit={e => {
                    e.preventDefault();

                    throttle(textValue, setApiSettings);
                }}>
                <div className="flex flex-col items-center justify-center gap-2">
                    <textarea
                    maxLength={maxTextLength}
                    onChange={(e) => {
                        const value: string = e.currentTarget.value;

                        setTextValue(value);
                    }}
                    value={textValue} 
                    className="relative bg-white resize-none rounded-xl p-2 w-[90%] h-60
                    default-shadow input-style">
                    </textarea>
                    <span className={`${textValue.length >= maxTextLength && "text-red-500"}`}>
                        {textValue.length}/{maxTextLength}
                    </span>
                    <Button text="Submit" type="submit" />
                </div>
            </form>
        </>
    )
}

const listItems: Array<{text: string, toolTipText: string}> = [
    {text: "[NAME]", toolTipText: "The name of the user"}, 
    {text: "[USERNAME]", toolTipText: "The username/domain account of the user, e.g. example@company.domain.org"}, 
    {text: "[PASSWORD]", toolTipText: "The password of the user"}, 
];

function HowToUseText(): JSX.Element{
    return (
        <div className="absolute bg-white p-3 rounded-2xl default-shadow border-1 border-blue-400/50 z-5
        top-0 left-0 h-fit w-fit mt-23 mx-2">
            <span>
                Three keywords are scanned and replaced in a given text submission:
                    <ul className="pl-5">
                        {listItems.map((obj, i) => (
                            <li className="relative list-point pl-2 flex items-center gap-1"
                            key={i}>
                                {obj.text}
                                <ToolTip text={obj.toolTipText} />
                            </li>
                        ))}
                    </ul>
            </span>
            <span>
                Keywords not defined in the text will be ignored.
                <br/>
                The brackets and capital case <strong><i>are required</i></strong>.
            </span>
        </div>
    )
}

async function textSubmission(text: string, setApiSettings: SettingsData["setApiSettings"]): Promise<void>{
    const res = await updateSetting("text", text, "template");

    if(res.status == "success"){
        setApiSettings(prev => ({...prev, template: {...prev.template, text: text}}));
        toastSuccess("Updated text template");
    }else{
        toastError(res.message);
    }
}