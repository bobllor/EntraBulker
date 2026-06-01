import React, { JSX, useRef, useState } from "react";
import "../../../pywebview";
import OptionBase from "./OptionBase";
import { OptionProps } from "../types";
import { Response } from "../../../pywebviewTypes";
import { toastResponse } from "../../../toastUtils";
import { useAuthStore } from "./store/useAuthStore";
import { useGraphSettingStore } from "../store/useGraphSettingsStore";
import { throttler } from "../../../utils";
import Button from "../../ui/Button";
import { FaCheckCircle, FaMinusCircle } from "react-icons/fa";
import SliderButton from "../../ui/SliderButton";
import { ToolTip } from "../../ui/ToolTip";

const throttleAuthenticateOnClick = throttler(() => authenticateOnClick(), 1500);

function TextComponent({graphKeyValue}: {graphKeyValue: string}): JSX.Element{
    const [inputValue, setInputValue] = useState("");
    const inputRef = useRef(null);

    return (
        <form
        onSubmit={(e) => updateGraphId(e, graphKeyValue, inputValue)}>
            <input
            className="input-style rounded-xl py-1 px-2"
            onChange={(e) => setInputValue(e.currentTarget.value)}
            ref={inputRef}/>
        </form>
    )
}

const AUTH_BUTTON_WIDTH: number = 35;
function AuthenticateButton(): JSX.Element{
    const isAuthenticating = useAuthStore((st) => st.isAuthenticating);

    return (
        <>
            {!isAuthenticating 
            ? 
                <Button text="Sign-in" func={() => throttleAuthenticateOnClick()} type="button" width={AUTH_BUTTON_WIDTH} />
            : 
                <Button text="Signing-in..." type="button" width={AUTH_BUTTON_WIDTH} />
            } 
        </>
    )
}

function AuthenicationIcon({iconElement, tooltip}: {iconElement: JSX.Element, tooltip: string}): JSX.Element{
    return (
        <span 
        title={tooltip}
        className="p-1">
            {iconElement}
        </span>
    )
}

// TODO:
//  1. move this into a generic UI
//  2. add the function to update the key + Reader
function DropDown({defaultValue, dropOptions}: DropDownProps): JSX.Element{
    return (
        <select
        tabIndex={-1}
        defaultValue={defaultValue}>
            {dropOptions.map((opt) => (
                <option
                key={opt.value}
                value={opt.value}>
                    {opt.text}
                </option>
            ))}
        </select>
    )
}

type DropDownProps = {
    /**
     * The default value displayed on the menu. This must be equal to a defined
     * value in dropOptions.
     */
    defaultValue: string
    /**
     * An array of drop down entries. Each entry consists of the text to display on
     * the menu, and the value used to the backend call.
     */
    dropOptions: Array<DropDownOption>
}

type DropDownOption = {
    text: string
    value: any
}

const userTypeDropOptions: Array<DropDownOption> = [
    {
        text: "Guest",
        value: "Guest",
    },
    {
        text: "Member",
        value: "Member",
    },
];

export default function Graph(): JSX.Element{
    const authStatus = useAuthStore((st) => st.auth);
    const enableGraphStatus = useGraphSettingStore(st => st.values.enable_graph);
    const updateEnableGraphStatus = useGraphSettingStore(st => st.updateEnableGraphStatus);
    const userType = useGraphSettingStore(st => st.values.user_type);

    const options: Array<OptionProps> = [
        {
            label: "Client Application ID",
            element: <TextComponent graphKeyValue="client_id" />,
        },
        {
            label: "Tenant ID",
            element: <TextComponent graphKeyValue="tenant_id" />,
        },
        {
            label: "Enable Graph",
            element: <SliderButton func={(status) => updateEnableGraphStatus(status)} status={enableGraphStatus}/>,
        },
        {
            label: "User Type",
            element: <DropDown defaultValue={userType} dropOptions={userTypeDropOptions} />,
            optElement: <ToolTip text={`Applies to all users whose domain is not listed in "Ignore User Type"`} />,
            optElementDirection: "row",
        },
        {
            label: "Sign-in Account",
            element: <AuthenticateButton />,
            optElement: authStatus 
                ? <AuthenicationIcon iconElement={<FaCheckCircle color="green" />} tooltip="Authenticated" /> 
                : <AuthenicationIcon iconElement={<FaMinusCircle color="red" />} tooltip="Not authenticated" />,
            optElementDirection: "row",
        },
    ];

    return (
        <>
            <OptionBase options={options} title="Microsoft Graph" tooltipText="Microsoft Graph settings"/>
        </>
    )
}

/**
 * Starts the authentication process.
 */
async function authenticateOnClick(){
    const authStatus: boolean = useAuthStore.getState().auth;
    const setAuth = useAuthStore.getState().setAuthStatus;
    const setIsAuthenticating = useAuthStore.getState().setIsAuthenticating;
    setIsAuthenticating(true);

    const res: Response = await window.pywebview.api.authenticate_graph();

    toastResponse(res);
    if(res.status == "error"){
        if(authStatus){
            setAuth(false);
        }
    }

    if(!authStatus){
        setAuth(true);
    }

    setIsAuthenticating(false);
}

/**
 * Used to update the IDs of the Graph data: client ID and tenant ID.
 * @param e The form event
 * @param graphKeyValue The target key being changed
 * @param inputValue The new value the key is
 */
async function updateGraphId(e: React.FormEvent<HTMLFormElement>, graphKeyValue: string, inputValue: string){
    e.preventDefault();
    const READER_TYPE = "graph";
    
    // yes i know this is not good. not going to add a logging system...
    // not right now at least. Me - 5/31/2026
    console.log(`${graphKeyValue} value: ${inputValue}`);

    const res = await window.pywebview.api.update_reader(READER_TYPE, graphKeyValue, inputValue);
    console.log(res);
}
