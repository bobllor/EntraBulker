import { Dispatch, JSX } from "react";
import { useContext, createContext, useState } from "react";

const ModalContext = createContext<ModalProps>({
    showModal: false,
    revealModal: async () => false,
    setShowModal: () => {},
    confirmModal: () => {},
    declineModal: () => {},
    modalText: '',
    setModalText: () => {}
});

export const useModalContext = () => useContext(ModalContext);

export function ModalProvider({ children }: {children: JSX.Element}): JSX.Element {
    const [showModal, setShowModal] = useState<boolean>(false);
    const [modalPromise, setModalPromise] = useState<((T: boolean) => void)|null>(null);
    const [modalText, setModalText] = useState<string>('');

    function revealModal(text: string = ''): Promise<boolean>{
        setShowModal(true);

        setModalText(text);

        return new Promise((resolve) => {
            return setModalPromise(() => resolve);
        })
    }

    function confirmModal(): void{
        modalPromise!(true);
        setShowModal(false);
        setModalPromise(null);
    }

    function declineModal(): void{
        modalPromise!(false);
        setShowModal(false);
        setModalPromise(null);
    }

    const data: ModalProps = {
        showModal,
        revealModal,
        setShowModal,
        confirmModal,
        declineModal,
        modalText,
        setModalText
    }
    
    return (
        <>
            <ModalContext.Provider value={data}>
                {children}
            </ModalContext.Provider>
        </>
    )
}

type ModalProps = {
    showModal: boolean,
    revealModal: (text?: string) => Promise<boolean>,
    setShowModal: Dispatch<React.SetStateAction<boolean>>,
    confirmModal: () => void,
    declineModal: () => void,
    modalText: string,
    setModalText: Dispatch<React.SetStateAction<string>>,
}