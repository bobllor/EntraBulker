import { JSX } from "react";

export default function Form({ children }: FormProps): JSX.Element{
    return (
        <>
            <form
            className="overflow-x-hidden bg-white h-150 w-60">
                {children}
            </form>
        </>
    )
}

type FormProps = {
    children: React.ReactNode;
}