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
import DropDown from "../../ui/DropDown";
import { DropDownOption } from "../../ui/DropDown";
import InputField from "../../ui/InputField";

const throttleAuthenticateOnClick = throttler(() => authenticateOnClick(), 1500);

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

const userTypeDropOptions: Array<DropDownOption> = [
    {
        text: "Guest",
        value: "guest",
    },
    {
        text: "Member",
        value: "member",
    },
];

export default function Graph(): JSX.Element{
    const authStatus = useAuthStore((st) => st.auth);
    const enableGraphStatus = useGraphSettingStore(st => st.values.enable_graph);
    const setGraphValues = useGraphSettingStore(st => st.setGraphValues);
    const userType = useGraphSettingStore(st => st.values.user_type);

    const options: Array<OptionProps> = [
        {
            label: "Enable Graph",
            element: <SliderButton func={(status) => setGraphValues("enable_graph", !status)} status={enableGraphStatus}/>,
        },
        {
            label: "Client Application ID",
            element: <InputField preventDefault readerKey="client_id" 
                updateReaderFunc={(key, value) => setGraphValues(key, value)} />,
        },
        {
            label: "Tenant ID",
            element: <InputField preventDefault readerKey="tenant_id" 
                updateReaderFunc={(key, value) => setGraphValues(key, value)} />,
        },
        {
            label: "Member Type Domain CSV",
            element: <InputField preventDefault readerKey="member_type_domain_csv"
                updateReaderFunc={(key, value) => setGraphValues(key, value)} />,
            optElement: <ToolTip text="User domains that will always be Member type regardless of the User Type option" />,
            optElementDirection: "row",
        },
        {
            label: "User Type",
            element: <DropDown defaultValue={userType} dropOptions={userTypeDropOptions} 
                updateReaderFunc={(key, value) => setGraphValues(key, value)} readerKey="user_type" />,
            optElement: <ToolTip text={`Applies to all created users whose domain is not listed in "Member Type Domain CSV"`} />,
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
