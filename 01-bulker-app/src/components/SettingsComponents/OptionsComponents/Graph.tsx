import React, { JSX } from "react";
import "../../../pywebview";
import OptionBase from "./OptionBase";
import { OptionProps } from "../types";
import { Response } from "../../../pywebviewTypes";
import { toastError, toastResponse } from "../../../toastUtils";
import { useAuthStore } from "./store/useAuthStore";
import { useGraphSettingStore } from "../store/useGraphSettingsStore";
import { throttler } from "../../../utils";
import Button from "../../ui/Button";
import { FaCheck, FaCheckCircle, FaMinus, FaMinusCircle } from "react-icons/fa";
import SliderButton from "../../ui/SliderButton";
import { ToolTip } from "../../ui/ToolTip";
import DropDown from "../../ui/DropDown";
import { DropDownOption } from "../../ui/DropDown";
import InputField from "../../ui/InputField";
import DataText from "../../ui/DataText";
import { useShallow } from "zustand/react/shallow";

const throttleAuthenticateOnClick = throttler(() => authenticateOnClick(), 1500);

const AUTH_BUTTON_WIDTH: number = 35;
function AuthenticateButton({authStatus}: {authStatus: boolean}): JSX.Element{
    const isAuthenticating = useAuthStore((st) => st.isAuthenticating);

    return (
        <>
            {!isAuthenticating 
            ? 
                <Button disabled={authStatus} text="Sign In" 
                func={() => throttleAuthenticateOnClick()} type="button" width={AUTH_BUTTON_WIDTH} />
            : 
                <Button text="Signing in..." type="button" width={AUTH_BUTTON_WIDTH} />
            } 
        </>
    )
}

const throttleLogoutOnClick = throttler(() => logoutOnClick(), 1500);
const throttleClearCacheOnClick = throttler(() => clearGraphCacheOnClick(), 1500);

function LogoutButton({authStatus}: {authStatus: boolean}): JSX.Element{
    return (
        <Button disabled={!authStatus} title={!authStatus ? "Must be signed in" : ""}
        text="Logout" type="button" width={AUTH_BUTTON_WIDTH} func={() => throttleLogoutOnClick() }/>
    )
}

function AuthenicationIcon({iconElement, tooltip = ""}: {iconElement: JSX.Element, tooltip?: string}): JSX.Element{
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
    const { clientId, tenantId, domainCsvString } = useGraphSettingStore(useShallow(st => ({
        clientId: st.values.client_id,
        tenantId: st.values.tenant_id,
        domainCsvString: st.values.member_type_domain_csv,
    })));

    const options: Array<OptionProps> = [
        {
            label: "Enable Graph",
            element: <SliderButton func={(status) => setGraphValues("enable_graph", !status)} status={enableGraphStatus}/>,
        },
        {
            label: "Client Application ID",
            element: <InputField preventDefault readerKey="client_id" 
                updateReaderFunc={(key, value) => setGraphValues(key, value)} />,
            optElement: <DataText value={clientId} enableCopy={clientId != ""} justification="center" />,
        },
        {
            label: "Tenant ID",
            element: <InputField preventDefault readerKey="tenant_id" 
                updateReaderFunc={(key, value) => setGraphValues(key, value)} />,
            optElement: <DataText value={tenantId} enableCopy={clientId != ""} justification="center" />,
        },
        {
            label: "Member Type Domain CSV",
            element: <InputField preventDefault readerKey="member_type_domain_csv"
                updateReaderFunc={(key, value) => setGraphValues(key, value)} />,
            optElement: <DataText value={domainCsvString} justification="center" />
        },
        {
            label: "User Type",
            element: <DropDown defaultValue={userType} dropOptions={userTypeDropOptions} 
                updateReaderFunc={(key, value) => setGraphValues(key, value)} readerKey="user_type" />,
            optElement: <ToolTip text={`Applies to all created users whose domain is not listed in "Member Type Domain CSV"`} />,
            optElementDirection: "row",
        },
        {
            label: "Sign In",
            element: <AuthenticateButton authStatus={authStatus} />,
            optElement: <DataText value={authStatus ? "Authenticated" : "Not authenticated"} label="Status: "
                optValueElement={
                authStatus
                ? <AuthenicationIcon iconElement={<FaCheckCircle color="green" />} />
                : <AuthenicationIcon iconElement={<FaMinusCircle color="red" />} />
            }/>,
            optElementDirection: "col",
        },
        {
            label: "Sign Out",
            element: <LogoutButton authStatus={authStatus} />,
        },
        {
            label: "Clear cache",
            element: <Button text={"Clear Cache"} func={() => throttleClearCacheOnClick()} width={AUTH_BUTTON_WIDTH} />,
            optElement: <ToolTip text="Clears the stored Microsoft Graph cache and logs out, if used reauthentication is required" />,
            optElementDirection: "row",
        }
    ];

    return (
        <>
            <OptionBase options={options} title="Microsoft Graph" tooltipText="Microsoft Graph settings"/>
        </>
    )
}

/**
 * Clears the stored cache for Graph. This will also logout the user.
 */
async function clearGraphCacheOnClick(){
    const setAuth = useAuthStore.getState().setAuthStatus;

    try{
        const res: Response = await window.pywebview.api.clear_graph_cache();

        if(res.status != "error"){
            setAuth(false); 
        }

        toastResponse(res);
    }catch(e){
        console.error("An unknown error occurred", e);
    }
}

/**
 * Starts the authentication process.
 */
async function authenticateOnClick(){
    const authStatus: boolean = useAuthStore.getState().auth;
    const setAuth = useAuthStore.getState().setAuthStatus;
    const setIsAuthenticating = useAuthStore.getState().setIsAuthenticating;

    try{
        setIsAuthenticating(true);
        // a warning indicates an already existing authentication
        const res: Response = await window.pywebview.api.authenticate_graph();

        toastResponse(res);
        if(res.status == "error"){
            if(authStatus){
                setAuth(false);
            }
        }else{
            if(!authStatus){
                setAuth(true);
            }
        }
    }
    catch(error){
        console.log(error);
        toastError("An unknown error occurred, it has been logged");
    }
    finally{
        setIsAuthenticating(false);
    }
}

/**
 * Logout from Graph.
 */
async function logoutOnClick(){
    const setAuth = useAuthStore.getState().setAuthStatus;

    try{
        const res: Response = await window.pywebview.api.logout_graph();

        if(res.status != "error"){
            setAuth(false); 
        }

        toastResponse(res);
    }catch(e){
        console.log("An unknown error has occurred", e);
    }
}