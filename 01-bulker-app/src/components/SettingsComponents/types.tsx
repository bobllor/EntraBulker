import { JSX } from "react"

export type SettingsButton = {
    label: string,
    url: string,
    icon?: JSX.Element,
}

export type OptionProps = {
    label: string, // the option to be displayed
    element: JSX.Element, // the element to display after the label. this should be related to the backend call
    optElement?: JSX.Element, // an optional element that is displayed right next to the label.
    optElementDirection?: "row" | "col",
    justify?: "center" | "between" | "start" | "end",
}

export type OptionBaseProps = {
    title: string,
    tooltipText?: string,
    options?: Array<OptionProps>,
    element?: JSX.Element,
}

export type ReaderType = "opco" | "settings" | "excel";

export type OpcoMap = {
    id: string,
    opcoKey: string,
    value: string,
}

export type OpcoCard = {
    key: string,
    val: string,
}