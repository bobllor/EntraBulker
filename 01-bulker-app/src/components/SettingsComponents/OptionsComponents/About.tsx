import { JSX } from "react";
import { OptionProps } from "../types";
import OptionBase from "./OptionBase";
import { useMetaContext } from "../../../context/MetaContext";
import Button from "../../ui/Button";

const REPO_LINK = "https://github.com/bobllor/EntraBulker";
const ISSUES_LINK = "https://github.com/bobllor/EntraBulker/issues";
const LICENSE_LINK = "https://github.com/bobllor/EntraBulker/blob/main/LICENSE";
const DEVELOPER = "Tri Nguyen";

export default function About(): JSX.Element{
    const { version } = useMetaContext();

    const options: Array<OptionProps> = [
        {
            label: "Developed by",
            element: <span>{DEVELOPER}</span>,
        },
        {
            label: "Version",
            element: <span>{version}</span>,
        },
        {
            label: "Repository",
            element: <Button text={"Open"} width={20} func={() => window.open(REPO_LINK, "_blank")}/>,
        },
        {
            label: "Report an issue",
            element: <Button text={"Open"} width={20} func={() => window.open(ISSUES_LINK, "_blank")} />
        },
        {
            label: "License",
            element: <Button text={"Open"} width={20} func={() => window.open(LICENSE_LINK, "_blank")} />
        },
    ];

    return (
        <OptionBase options={options} title="About" />
    )
}