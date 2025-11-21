import { JSX } from "react";
import { OptionProps, ReaderType } from "../types";
import OptionBase from "./OptionBase";
import { onSubmitText } from "../functions";
import { useSettingsContext } from "../../../context/SettingsContext";

const TextComponent = ({name, readerType}: {name: string, readerType: ReaderType}) => (
    <form
    onSubmit={e => onSubmitText(e, readerType)}>
        <input
        name={name}
        className="border-1 rounded-xl py-1 px-2 outline-none"
        type="text" />
    </form>
)

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
const tooltipText: string = "Changes the column names of the Excel file for parsing.";

export default function HeadersMapping(): JSX.Element{ 
    const {headers} = useSettingsContext();

    const options: Array<OptionProps> = [
        {
            label: "Name", 
            element: <TextComponent name={"name"} readerType={readerType} />, 
            optElement: CurrentValue(headers.name),
        },
        {
            label: "Operating Company", 
            element: <TextComponent name={"opco"} readerType={readerType} />,
            optElement: CurrentValue(headers.opco),
        },
    ]

    return (
        <>
            <OptionBase options={options} title={title} tooltipText={tooltipText} />
        </>
    )
}