import { JSX } from "react";

/**
 * A button component. 
 * @param text The text of the button 
 * @param bg Tailwind class string for the background of the button, by default it is bg-blue-500
 * @param bgHover Tailwind class string for the hover background of the button, by default it is bg-blue-400 
 * @param paddingX Number representing the padding amount for the X-axis
 * @param paddingY Number representing the padding amount for the Y-axis
 * @param type The button type
 * @param func The function used when the button is clicked, by default it is `undefined`
 */
export default function Button(
    {text, bg = "bg-blue-500", bgHover = "bg-blue-400", 
    paddingX = 2, paddingY = 2, type = "submit", func = undefined}: ButtonProps): JSX.Element{

    return (
        <>
            <button
            onClick={() => {
                if(func){
                    func();
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
}