import { JSX, useEffect, useMemo } from "react";
import { useModalContext } from "../context/ModalContext";
import { FaTimes } from "react-icons/fa";

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
        <div className="w-screen h-screen absolute flex justify-center items-center z-5">
            <div className="flex flex-col p-10 rounded-xl border-1 border-gray-300 gap-9
            bg-white w-100 h-50 z-4 absolute justify-center items-center default-shadow">
                <div className="absolute top-1 right-1 rounded-xl hover:bg-gray-500"
                onClick={() => declineModal()}>
                    <div className="flex justify-center items-center p-2">
                        <FaTimes />
                    </div>
                </div>
                <div>
                    <span>{modalText}</span>
                </div>
                <div
                className="flex gap-5">
                    {buttons.map((obj, i) => (
                    <button
                    className="bg-blue-500 p-2 rounded-xl w-30 h-10 hover:bg-blue-400 text-white default-shadow" 
                    key={i} onClick={obj.func}>
                        {obj.name}
                    </button>
                    ))}
                </div>
            </div>
        </div>
        </>
    )
}