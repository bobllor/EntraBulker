import { JSX, useRef, useState } from "react";

export default function InputField({preventDefault = false, readerKey, updateReaderFunc}: InputFieldProps): JSX.Element{
    const [inputValue, setInputValue] = useState("");
    const inputRef = useRef<HTMLInputElement>(null);

    return (
        <form
        onSubmit={(e) => {
                if(preventDefault){
                    e.preventDefault();
                }

                updateReaderFunc(readerKey, inputValue);
                
                if(inputRef.current){
                    inputRef.current.value = "";
                    setInputValue("");
                    inputRef.current.focus();
                }
            }}>
            <input
            className="input-style rounded-xl py-1 px-2"
            onChange={(e) => setInputValue(e.currentTarget.value)}
            ref={inputRef}/>
        </form>
    )
}

type InputFieldProps = {
    /**
     * Used to prevent the event that occurs with a default form submission.
     * By default it is false.
     */
    preventDefault: boolean
    /**
     * The target Reader key that is being updated. This is used in the updateReaderFunc.
     */
    readerKey: string
    /**
     * The function used to update the Reader with the target key and the input value of the
     * input field.
     * 
     * @param key The target key
     * @param value The input field value
     * @returns 
     */
    updateReaderFunc: (key: string, value: string) => void
}