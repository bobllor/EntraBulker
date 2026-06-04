import { JSX } from "react";
import { toastSuccess } from "../../toastUtils";

/**
 * Creates a span JSX element that displays the value given.
 * @returns A JSX element
 */
export default function DataText({label = "", maxValueLength = 30, value, 
    enableCopy = false, optValueElement, justification = "start"}: DataTextProps): JSX.Element{
    return (
        <div className="flex items-center w-60">
            <span
            onClick={() => {
                if(enableCopy){
                    navigator.clipboard.writeText(value).then(() => {
                        toastSuccess("Copied to clipboard");
                    });
                }
            }}
            className={`text-xs text-ellipsis overflow-hidden whitespace-nowrap w-fit max-w-68 h-4
                block items-center justify-${justification} rounded-xl px-1
                ${enableCopy && "hover:bg-gray-500/25"}`}
            title={value.length > maxValueLength ? value : ""}>
                {label + value}
            </span>
            {optValueElement != undefined && optValueElement}
        </div>
    )
}

type DataTextProps = {
    /**
     * The text before the value. This can be empty.
     */
    label?: string
    /**
     * The text after the label. This is often a reactive element to display updates.
     */
    value: string
    /**
     * An optional element that displays after the value. This is often an icon or image.
     */
    optValueElement?: JSX.Element
    /**
     * The maximum length of the value text before it cuts off with ellipsis.
     * This does not include the label concatenation.
     * This is optional and defaults to 20 characters.
     */
    maxValueLength?: number
    /**
     * The justification of the elements in the span. By default it is start.
     */
    justification?: "start" | "center"
    /**
     * Flag used to allow copying to the clipboard by clicking on the element. This
     * also will a hover effect when the mouse is over. By default it is false.
     */
    enableCopy?: boolean
}