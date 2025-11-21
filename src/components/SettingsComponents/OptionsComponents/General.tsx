import { JSX } from "react";
import OptionBase from "./OptionBase";
import { OptionProps } from "../types";
import SliderButton from "../../ui/SliderButton";
import Button from "../../ui/Button";
import "../../../pywebview";
import { useSettingsContext } from "../../../context/SettingsContext";
import { setSetting, setOutputDir, setTextGenerationState, updateFormattingKey } from "../functions";
import DropDown, { DropDownObject } from "../../ui/DropDown";

const title: string = "General";
const tooltipText: string = "General settings for the program.";
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
        },
        {
            label: "Format Type", 
            element: <DropDown obj={formatTypeArray} 
                objId="format_type" defaultValue={apiSettings.format.format_type} 
                func={(key: string, value: any) => {updateFormattingKey(key, value, setApiSettings)}} />
        },
        {
            label: "Format Style", element: <DropDown obj={formatStyleArray} 
                objId="format_style" defaultValue={apiSettings.format.format_style} 
                func={(key: string, value: any) => {updateFormattingKey(key, value, setApiSettings)}} />
        },
        {
            label: "Format Case", 
            element: <DropDown obj={formatCaseArray} 
                objId="format_case" defaultValue={apiSettings.format.format_case} 
                func={(key: string, value: any) => {updateFormattingKey(key, value, setApiSettings)}} />
        },
        {
            label: "Generate Text", 
            element: <SliderButton status={apiSettings.template.enabled}
                func={(status: boolean) => setTextGenerationState(status, setApiSettings)}/>,
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