import { JSX, useState } from "react";
import { updateSetting } from "../../pywebviewFunctions";

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

/**
 * 
 * @param func The function returned by the closure, this requires a `targetKey`, the `value` replacing the targetKey's value,
 * an `updaterFunc` which is expected to be a setter function from useState, and optionally a `parent`, which by default is
 * undefined, used for targeting nested keys.
 * @param timeout A timeout number, by default it is `700` ms.
 */
function debouncer(
    func: (targetKey: string, value: any, updaterFunc: (number: number) => any, parent?: string) => void | Promise<any>,
    timeout: number = 700){
    let timer: number | undefined;

    return (targetKey: string, value: any, updaterFunc: (number: number) => any, parent?: string) => {
        clearTimeout(timer);

        timer = setTimeout(() => {
            func(targetKey, value, updaterFunc, parent);
        }, timeout);
    }
}