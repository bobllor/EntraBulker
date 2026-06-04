import { JSX, useRef } from "react";
import { debouncer, throttler } from "../../utils";

/**
 * A button component. 
 * 
 * If closures are needed, then a function must be used. 
 * 
 * If disabled is true, then the button will be gray and unusuable until the condition is false.
 */
export default function Button(
    {text, bg = "bg-blue-500", bgHover = "bg-blue-400", 
    paddingX = 2, paddingY = 2, type = "submit", func = undefined,
    closureOpt = undefined, width = 0, height = 0, disabled = false, title = ""}: ButtonProps): JSX.Element{
    const closureRef = useRef(getClosure(closureOpt));

    const widthCss = width != 0 ? `w-${width}` : "";
    const heightCss = height != 0 ? `h-${height}` : "";

    return (
        <>
            <button
            onClick={() => {
                if(func){
                    if(closureRef.current != undefined){
                        closureRef.current(func); 
                    }else{
                        func();
                    }
                }
            }}
            title={title}
            tabIndex={-1}
            className={`px-${paddingX} py-${paddingY} rounded-xl 
            ${!disabled ? bg : "bg-gray-500/50"} ${!disabled && `text-white hover:${bgHover}`}
            border-1 default-shadow border-gray-400/60 ${widthCss} ${heightCss} flex justify-center items-center`}
            disabled={disabled}
            type={type}>
                {text}
            </button>
        </>
    )
}

type ButtonProps = {
    /**
     * The value displayed inside the button. It can be a text string or an
     * JSX element.
     */
    text: string | JSX.Element,
    /**
     * The hover text of the button.
     */
    title?: string,
    bg?: string,
    bgHover?: string,
    paddingX?: number,
    paddingY?: number,
    /**
     * The width of the button in rem. If 0 or not given the button will match
     * the size of the contents automatically.
     */
    width?: number,
    /**
     * The height of the button in rem. If 0 or not given the button will match
     * the size of the contents automatically.
     */
    height?: number,
    func?: () => any | undefined,
    type?: "submit" | "reset" | "button" | undefined,
    closureOpt?: ClosureProps,
    disabled?: boolean,
}

type ClosureProps = {
    type: "debounce" | "throttle",
    timeout: number,
}

/**
 * Gets the throttler or debouncer closure function.
 * @param closureOpt The ClosureProp object.
 * @returns The throttler or debouncer closure function, or if closureOpt is undefined then undefined.
 */
function getClosure(
    closureOpt?: ClosureProps): ((func: () => any) => any) | undefined{
    if(closureOpt == undefined){
        return undefined;
    }
    let closureFunc = throttler((func: () => any) => func(), closureOpt.timeout)

    if(closureOpt.type == "debounce"){
        closureFunc = debouncer((func: () => any) => func(), closureOpt.timeout)
    }

    return closureFunc
}