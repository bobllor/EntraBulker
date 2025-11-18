import React, { JSX, useRef } from "react";
import { SettingsButton } from "./types";
import Button from "./NavigationComponents/Button";
import { FaTimes } from "react-icons/fa";
import { useDismissRoute } from "../../hooks";

export default function Navigation({
    buttons, selectedSetting, setSelectedSetting, setShowSetting}: NavigationProps): JSX.Element{
    
    const closeRef = useRef<HTMLDivElement|null>(null);

    useDismissRoute(closeRef, setShowSetting);

    return (
        <div className={`h-full w-[33%] bg-gray-500/60 absolute 
        settings-left-panel p-2`}>
            <div className="flex items-center justify-start px-1">
                <div className="hover:bg-gray-500 rounded-xl p-1 mb-1"
                ref={closeRef}>
                    <FaTimes size={25} />
                </div>
            </div>
            {buttons.map((ele, i) => (
                <React.Fragment
                key={i}>
                    <Button opts={ele}
                    selectedSetting={selectedSetting} setSelectedSetting={setSelectedSetting} /> 
                </React.Fragment>
            ))}
        </div>
    )
}

type NavigationProps = {
    buttons: Array<SettingsButton>,
    selectedSetting: string,
    setSelectedSetting: React.Dispatch<React.SetStateAction<string>>,
    setShowSetting: React.Dispatch<React.SetStateAction<boolean>>,
}