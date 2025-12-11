import React from "react"

export type SliderButtonProps = {
    status: boolean,
    statusSetter: React.Dispatch<React.SetStateAction<boolean>>,
}