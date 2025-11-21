import React, { JSX, useEffect, useState } from "react";

export default function SliderButton({func, status}: 
    {func: (status: boolean) => void, status: boolean}): JSX.Element{

    return (
        <>
            <div
            onClick={() => func(status)}
            className={`flex rounded-3xl items-center w-10 h-6 relative px-0.5
                ${!status ? "bg-white justify-start" : "bg-blue-500 justify-end"}
                transition-all duration-400`}>
                <div 
                className="rounded-2xl bg-blue-300 w-5 h-5 "/>
            </div>
        </>
    )
}