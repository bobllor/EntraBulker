import { JSX, useRef, useState } from "react";
import { OptionProps, ReaderType } from "../types";
import OptionBase from "./OptionBase";
import { updateExcelReader } from "../functions";
import { useSettingsContext } from "../../../context/SettingsContext";
import { ToolTip } from "../../ui/ToolTip";

function TextComponent({name, readerType, toolTipText}: TextComponentProps): JSX.Element {
    const [inputValue, setInputValue] = useState<string>("");
    const inputRef = useRef<HTMLInputElement>(null);

    const {setUpdateHeaders} = useSettingsContext();

    return (
        <>
            <form
            className="flex justify-center items-center"
            onSubmit={e => {
                e.preventDefault(); 
                
                updateExcelReader(name, inputValue, readerType).then((status) => {
                    if(status){
                        if(inputRef.current){
                            inputRef.current.value = "";
                            inputRef.current.focus();
                        }

                        setUpdateHeaders(true);
                    };
                })}}>
                    {toolTipText != "" && 
                        <div className="flex">
                            <ToolTip text={toolTipText!} />
                        </div>
                    }
                    <input
                    name={name}
                    ref={inputRef}
                    onChange={e => setInputValue(e.currentTarget.value)}
                    className="input-style rounded-xl py-1 px-2"
                    type="text" />
            </form>
        </>
    )
}

const CurrentValue = (currVal: string) => {
    const maxLength: number = 20;
    const label: string = "Value: "

    return (
        <span
        className="text-ellipsis"
        title={currVal.length > maxLength ? currVal : ""}>
            {label + currVal}
        </span>
    )
}

const title: string = "Headers";
const readerType: ReaderType = "excel";
const tooltipText: string = "Modify the column names of the Excel file for parsing";

export default function HeadersMapping(): JSX.Element{ 
    const {headers} = useSettingsContext();

    const options: Array<OptionProps> = [
        {
            label: "Name", 
            element: <TextComponent name={"name"} readerType={readerType}
                toolTipText="The header for the name of the user"/>, 
            optElement: CurrentValue(headers.name),
        },
        {
            label: "Organization", 
            element: <TextComponent name={"opco"} readerType={readerType}
                toolTipText="The header of the organization for the user"/>,
            optElement: CurrentValue(headers.opco),
        },
    ]

    return (
        <>
            <OptionBase options={options} title={title} tooltipText={tooltipText} />
        </>
    )
}

type TextComponentProps = {
    name: string, 
    readerType: ReaderType, 
    toolTipText?: string,        
}