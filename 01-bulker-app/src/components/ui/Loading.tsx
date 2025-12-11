import { JSX } from "react";

export default function Loading(): JSX.Element{
    return (
        <div className="flex w-full justify-center items-center">
            <div className="w-10 h-10 border-4 border-blue-300 rounded-2xl loader shadow-2xl" />
        </div>
    )
}