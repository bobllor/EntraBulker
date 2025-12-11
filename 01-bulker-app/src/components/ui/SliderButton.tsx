import { JSX } from "react";

/**
 * Creates a slider button component, it requires a function that takes a boolean as an argument and the
 * status of true/false state of the button state itself.
 */
export default function SliderButton({func, status}: 
    {func: (status: boolean) => void, status: boolean}): JSX.Element{

    return (
        <>
            <div
            onClick={() => func(status)}
            className={`flex rounded-3xl items-center w-10 h-6 relative px-0.5 default-shadow
                ${!status ? "bg-white justify-start" : "bg-blue-500 justify-end"}
                transition-all duration-400 border-1 border-gray-400/40`}>
                <div 
                className="rounded-2xl bg-blue-300 w-5 h-5 "/>
            </div>
        </>
    )
}