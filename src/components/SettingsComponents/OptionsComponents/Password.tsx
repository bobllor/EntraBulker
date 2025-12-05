import { JSX, useState } from "react";
import OptionBase from "./OptionBase";
import { OptionProps } from "../types";
import { useSettingsContext } from "../../../context/SettingsContext";
import SliderButton from "../../ui/SliderButton";
import { setSetting } from "../functions";
import SliderRange from "../../ui/SliderRange";
import { generatePassword } from "../../../pywebviewFunctions";
import { FaClipboard, FaSync } from "react-icons/fa";
import { toastSuccess } from "../../../toastUtils";
import { throttler } from "../../../utils";

const toolTipText: string = "Password settings";
const PARENT_KEY: string = "password";

export default function Password(): JSX.Element{
    const { apiSettings, setApiSettings } = useSettingsContext();

    const options: Array<OptionProps> = [
        {
            label: "Generate a password", 
            element: <GeneratePassword />, 
            justify: "between"
        },
        {
            label: "Password length", 
            element: <SliderRange targetKey="length" baseValue={apiSettings.password.length} 
                parent="password" 
                updaterFunc={(number: number) => setApiSettings
                    (prev => ({...prev, password: {...prev.password, length: number}}))} />,
        },
        {
            label: "Include uppercase letters", 
            element: <SliderButton func={(status: boolean) => {
                setSetting("use_uppercase", !status, 
                    () => {setApiSettings(prev => ({...prev, password: {...prev.password, use_uppercase: !status}}))},
                    PARENT_KEY
                );
            }} 
            status={apiSettings.password.use_uppercase}/>
        },
        {
            label: "Include punctuations", 
            element: <SliderButton func={(status: boolean) => {
                setSetting("use_punctuations", !status, 
                    () => {setApiSettings(prev => ({...prev, password: {...prev.password, use_punctuations: !status}}))},
                    PARENT_KEY
                );
            }} 
            status={apiSettings.password.use_punctuations}/>
        },
    ];

    return (
        <>
            <OptionBase options={options} title="Password" tooltipText={toolTipText} />
        </>
    )
}

const iconStyle: string = "p-2 rounded-xl hover:bg-gray-400";
const passwordThrottler = throttler(
    (updaterFunc: (...args: any) => any) => generatePassword().then((pw) => updaterFunc(pw))
);

function GeneratePassword(): JSX.Element{
    const [password, setPassword] = useState<string>("");

    return (
        <div className="flex items-center justify-between w-full">
            <div className={`transition-all`}>
                <div className="bg-white p-2 input-style rounded-2xl w-95 flex items-center
                justify-between">
                    <span>
                        {password}
                    </span>
                    <div className="flex items-center">
                        <span 
                        className={iconStyle}
                        title="Copy to clipboard"
                        onClick={() => {
                            if(password != ""){
                                navigator.clipboard.writeText(password).then(() => {
                                    toastSuccess("Copied to clipboard")
                                });
                            }
                        }}>
                            <FaClipboard size={18}/>
                        </span>
                        <span
                        title="Generate password"
                        className={iconStyle}
                        onClick={() => passwordThrottler(setPassword)}>
                            <FaSync size={18} />
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}