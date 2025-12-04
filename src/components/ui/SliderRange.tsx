import { JSX, useState } from "react";
import { updateSetting } from "../../pywebviewFunctions";
import { debouncer } from "../../utils";

const sliderDebouncer = debouncer(
    (key: string, value: any, updaterFunc: (number: number) => any, parent?: string) => {
        updateSetting(key, value, parent).then(() => updaterFunc(value));
    });

const minLength: number = 7;
const maxLength: number = 30;

/**
 * A slider range component. It requires a target key, a base value, and optionally a parent to update the Settings contents. 
 * 
 * The updaterFunc is required to update the state of the Settings. This is expected to take a number argument.
 */
export default function SliderRange({targetKey, baseValue, parent = undefined, updaterFunc}: SliderProps): JSX.Element{
    const [sliderValue, setSliderValue] = useState<number>(baseValue);


    return (
        <div className="flex items-center gap-2">
            <span>{sliderValue}</span>
            <input 
            defaultValue={sliderValue}
            onChange={(e) => {
                const value: number = Number(e.currentTarget.value);
                setSliderValue(Number(e.currentTarget.value));

                sliderDebouncer(targetKey, value, updaterFunc, parent);
            }}
            min={minLength}
            max={maxLength}
            type="range" />
        </div>
    )
}

export type SliderProps = {
    targetKey: string,
    baseValue: number,
    updaterFunc: (number: number) => any,
    parent?: string,
}