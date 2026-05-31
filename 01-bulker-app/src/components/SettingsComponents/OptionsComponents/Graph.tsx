import React, { JSX, useRef, useState } from "react";
import "../../../pywebview";
import OptionBase from "./OptionBase";
import { OptionProps } from "../types";
import { Response } from "../../../pywebviewTypes";
import { toastResponse } from "../../../toastUtils";
import { useAuthStore } from "./store/useAuthStore";
import { throttler } from "../../../utils";
import Button from "../../ui/Button";
import { FaCheckCircle, FaMinusCircle } from "react-icons/fa";

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

async function updateGraphId(e: React.FormEvent<HTMLFormElement>, graphKeyValue: string, inputValue: string){
    e.preventDefault();
    const READER_TYPE = "graph";
    
    // yes i know this is not good. not going to add a logging system...
    // not right now at least. Me - 5/31/2026
    console.log(`${graphKeyValue} value: ${inputValue}`);

    const res = await window.pywebview.api.update_key(READER_TYPE, graphKeyValue, inputValue);
    console.log(res);
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

export default function Graph(): JSX.Element{
    const authStatus = useAuthStore((st) => st.auth);

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