import { JSX } from "react";

/**
 * Creates a new DropDown menu for use.
 * @returns 
 */
export default function DropDown({defaultValue, dropOptions, updateReaderFunc, readerKey}: DropDownProps): JSX.Element{
    return (
        <select
        className="outline-1 min-w-[30%] max-w-[30%] rounded-sm p-1"
        onChange={(e) => updateReaderFunc(readerKey, e.currentTarget.value)}
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
    /**
     * The key of the Reader that will be updated. This is used with updateReadFunc.
     */
    readerKey: string
    /**
     * An update function that updates the value of the reader. It is expected that this
     * will also update the value in the context.
     * 
     * @param key The target key to update
     * @param value The value of the key to update to- the drop down option value
     * @returns 
     */
    updateReaderFunc: (key: string, value: string) => void
}

export type DropDownOption = {
    text: string
    value: any
}
