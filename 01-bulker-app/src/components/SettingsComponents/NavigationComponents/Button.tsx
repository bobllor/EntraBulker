import { JSX } from "react";
import { SettingsButton } from "../types";
import { useLocation, useNavigate } from "react-router";

export default function Button({opts, selectedSetting, setSelectedSetting}: ButtonProps): JSX.Element{
    let navigate = useNavigate();
    let location = useLocation();

    function handleClick(){
        if(opts.label == selectedSetting){
            return;
        }

        setSelectedSetting(opts.label);
        navigate(opts.url, {replace: true, state: {previousLocation: location.state?.previousLocation}});
    }
    return (
        <div className={`w-full h-8 rounded-xl 
        ${opts.label == selectedSetting ? "bg-gray-300" : "hover:bg-gray-300"} 
        flex items-center p-3 gap-2`}
        onClick={handleClick}>
            <div className="flex items-center">
                {opts.icon != null && opts.icon}
            </div>
            <div className="flex items-center">
                {opts.label}
            </div>
        </div>
    )
}

type ButtonProps = {
    opts: SettingsButton,
    selectedSetting: string,
    setSelectedSetting: React.Dispatch<React.SetStateAction<string>>,
}