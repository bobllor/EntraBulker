import { JSX } from "react";
import { OptionBaseProps, OptionProps } from "../types";
import { ToolTip } from "../../ui/ToolTip";

export default function OptionBase({options = [], tooltipText, title, element}: OptionBaseProps): JSX.Element{
    return (
        <>
            <div className="border-b-2 m-2 p-2 flex items-center">
                <h2 className="text-lg">
                    {title}
                </h2>
                {tooltipText && <ToolTip text={tooltipText} />}
            </div>
            <div className="overflow-y-auto h-[inherit]">
                {options.length > 0 && !element ? options.map((opt, i) => (
                    <div 
                    key={i}
                    className={getClassName(opt.justify)}>
                        <div className="flex flex-col">
                            {opt.label}
                            {opt.optElement && opt.optElement}
                        </div>
                        {opt.element}
                    </div>
                )) : options.length < 1 && element ? element : <></>}
            </div>
        </>
    )
}

/**
 * Generates the class name based off of justify. By default it will always be justify-between if undefined.
 * @param justify - The justification of the flex box.
 * @returns className
 */
function getClassName(justify: OptionProps["justify"] | undefined): string{
    let optionClassName: string = "flex items-center border-b-1 m-2 p-4 text-sm gap-3";

    switch (justify) {
        case "center":
            optionClassName = `${optionClassName} justify-center`;
            break;
        case "end":
            optionClassName = `${optionClassName} justify-end`;
            break;
        case "start":
            optionClassName = `${optionClassName} justify-start`;
            break;
        default:
            optionClassName = `${optionClassName} justify-between`;
            break;
    }

    return optionClassName;
}