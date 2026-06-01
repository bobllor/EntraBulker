import { JSX } from "react";
import OptionBase from "./OptionBase";
import { OptionProps } from "../types";
import SliderButton from "../../ui/SliderButton";
import Button from "../../ui/Button";
import "../../../pywebview";
import { useSettingsContext } from "../../../context/SettingsContext";
import { setSetting, setOutputDir, setTextGenerationState, updateFormattingKey } from "../functions";
import { ToolTip } from "../../ui/ToolTip";
import { FormatCase, FormatStyle, FormatType } from "../../../pywebviewTypes";

const title: string = "General";
const tooltipText: string = "General settings for the program";
const formatTypeArray: Array<DropDownObject> = [
    {value: "period", text: "Period"},
    {value: "no space", text: "No Space"},
];
const formatStyleArray: Array<DropDownObject> = [
    {value: "first last", text: "First Last"},
    {value: "f last", text: "F. Last"},
    {value: "first l", text: "First L."},
];
const formatCaseArray: Array<DropDownObject> = [
    {value: "lower", text: "Lowercase"},
    {value: "upper", text: "Uppercase"},
    {value: "title", text: "Title Case"},
];

export default function General(): JSX.Element{
    const {apiSettings, setApiSettings} = useSettingsContext();

    const options: Array<OptionProps> = [
        {
            label: "Output Folder", 
            element: <Button text="Select Folder" paddingX={2} paddingY={2} 
                func={() => setOutputDir(setApiSettings)} type="button" />, 
            optElement: <OutputFolder outputDir={apiSettings.output_dir} />,
        },
        {
            label: "Flatten CSV", 
            element: <SliderButton status={apiSettings.flatten_csv}
                func={(status: boolean) => setSetting("flatten_csv", !status, () => {
                    setApiSettings(prev => ({...prev, flatten_csv: !status}));
                })} />,
            optElement: <ToolTip 
            text="Flattens uploaded files into a single CSV file and if Generate Text is enabled, a single directory" />,
            optElementDirection: "row",
        },
        {
            label: "Generate Text", 
            element: <SliderButton status={apiSettings.template.enabled}
                func={(status: boolean) => setTextGenerationState(status, setApiSettings)}/>,
            optElement: <ToolTip text="Enables text generation for each user in the file based on a template" />,
            optElementDirection: "row",
        },
        {
            label: "First/Last Name Headers", 
            element: <SliderButton status={apiSettings.two_name_column_support}
                func={(status: boolean) => setSetting("two_name_column_support", !status, () => {
                    setApiSettings(prev => ({...prev, two_name_column_support: !status}));
                })}/>,
            optElement: <ToolTip text="Enables support for First and Last Name columns instead of a single Full Name column"/>,
            optElementDirection: "row",
        },
        {
            label: "Format Type", 
            element: <DropDownFormatting obj={formatTypeArray} 
                objId="format_type" defaultValue={apiSettings.format.format_type} 
                func={(key: string, value: any) => {updateFormattingKey(key, value, setApiSettings)}} />,
            optElement: <ToolTip text="Formats the username to the given type, e.g. First.Last or FirstLast" />,
            optElementDirection: "row",
        },
        {
            label: "Format Style", element: <DropDownFormatting obj={formatStyleArray} 
                objId="format_style" defaultValue={apiSettings.format.format_style} 
                func={(key: string, value: any) => {updateFormattingKey(key, value, setApiSettings)}} />,
            optElement: <ToolTip text="Chooses the formatting style of how the username is generated, e.g. F.Last or First.Last" />,
            optElementDirection: "row",
        },
        {
            label: "Format Case", 
            element: <DropDownFormatting obj={formatCaseArray} 
                objId="format_case" defaultValue={apiSettings.format.format_case} 
                func={(key: string, value: any) => {updateFormattingKey(key, value, setApiSettings)}} />,
            optElement: <ToolTip text="Affects the casing of the username" />,
            optElementDirection: "row",
        },
    ]

    return (
        <>
            <OptionBase options={options} title={title} tooltipText={tooltipText} />
        </>
    )
}

function OutputFolder({outputDir}: {outputDir: string}): JSX.Element{
    const maxLength: number = 20;
    const label: string = "Value: ";

    return (
        <>
            <span
            className="text-ellipsis"
            title={outputDir.length >= maxLength ? outputDir : ""}>
                {label + outputDir}
            </span>        
        </>
    )
}

function DropDownFormatting({obj, objId, defaultValue, func}: DropDownProps): JSX.Element{
    return (
        <>
            <select
            className="outline-1 min-w-[30%] max-w-[30%] rounded-sm p-1"
            tabIndex={-1}
            defaultValue={defaultValue}
            onChange={(e) => handleOnChangeSelect(e, objId, func)}>
                {obj.map((ele) => (
                    <option 
                    key={ele.value}
                    value={ele.value}>{ele.text}</option>
                ))}
            </select>
        </>
    )
}

async function handleOnChangeSelect(
    e: React.ChangeEvent<HTMLSelectElement>, 
    key: string,
    func?: DropDownProps["func"],){
    const selectedValue: string = e.currentTarget.value;

    if(func){
        func(key, selectedValue);
    }
}

type DropDownProps = {
    obj: Array<DropDownObject>,
    objId: string,
    defaultValue: DropDownObject["value"],
    func?: (key: string, value: any) => void | undefined,
}

export type DropDownObject = {
    value: FormatCase | FormatStyle | FormatType,
    text: string,
}