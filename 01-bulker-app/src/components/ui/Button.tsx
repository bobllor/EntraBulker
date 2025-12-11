import { JSX, useRef } from "react";
import { debouncer, throttler } from "../../utils";

/**
 * A button component. 
 * 
 * If closures are needed, then a function must be used. 
 */
export default function Button(
    {text, bg = "bg-blue-500", bgHover = "bg-blue-400", 
    paddingX = 2, paddingY = 2, type = "submit", func = undefined,
    closureOpt = undefined}: ButtonProps): JSX.Element{

    const closureRef = useRef(getClosure(closureOpt));

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
            tabIndex={-1}
            className={`px-${paddingX} py-${paddingY} rounded-xl ${bg} text-white hover:${bgHover}
            border-1 default-shadow border-gray-400/60`}
            type={type}>
                {text}
            </button>
        </>
    )
}

type ButtonProps = {
    text: string,
    bg?: string,
    bgHover?: string,
    paddingX?: number,
    paddingY?: number,
    func?: () => any | undefined,
    type?: "submit" | "reset" | "button" | undefined,
    closureOpt?: ClosureProps,
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