import { JSX } from "react";
import { Outlet } from "react-router";

export default function Options(): JSX.Element{
    return (
        <>
            <div className={`h-full w-[67%] bg-white absolute right-0
            settings-right-panel overflow-hidden`}>
                <Outlet />
            </div>
        </>
    )
}