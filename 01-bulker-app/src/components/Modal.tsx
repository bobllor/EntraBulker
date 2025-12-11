import { JSX, useEffect, useMemo } from "react";
import { useModalContext } from "../context/ModalContext";

function handleKeyDown(event: KeyboardEvent, declineFunc: () => void): void{
    if(event.key == 'Escape'){
        declineFunc();
    }
}

export default function Modal(): JSX.Element{
    const {
        modalText, 
        confirmModal, 
        declineModal, 
    } = useModalContext();

    const buttons: Array<{name: string, func: () => void}> = useMemo(() => {
        return [
            {name: 'Confirm', func: confirmModal},
            {name: 'Cancel', func: declineModal}
        ]
    }, [])

    useEffect(() => {
        window.addEventListener('keydown', e => handleKeyDown(e, declineModal));

        return(() => {
            window.removeEventListener('keydown', e => handleKeyDown(e, declineModal));
        })
    }, [])

    return (
        <>
            <div className="flex flex-col p-10 rounded-xl border-1 gap-9
            bg-white w-100 h-50 z-4 absolute justify-center items-center">
                <div>
                    <span>{modalText}</span>
                </div>
                <div
                className="flex gap-10">
                    {buttons.map((obj, i) => (
                    <button
                    className="bg-blue-500/90 p-2 rounded-xl w-30 h-10 hover:bg-blue-400/60 text-white" 
                    key={i} onClick={obj.func}>
                        {obj.name}
                    </button>
                    ))}
                </div>
            </div>
        </>
    )
}