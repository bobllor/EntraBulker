import { JSX } from "react";

export default function ProgressText({text, textColor = "text-black"}: ProgressTextProps): JSX.Element{
    return (
        <div className={`${textColor} flex items-center text-wrap px-5 text-sm`}>
            {text}
        </div>
    )
}

type ProgressTextProps = {
    text: string,
    textColor?: string,
}