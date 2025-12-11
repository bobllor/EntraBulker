import { JSX } from "react";
import { useContext, createContext, useState } from "react";
import { useInitMeta } from "./hooks";

const MetaContext = createContext<MetaData>({
    version: "",
});

export const useMetaContext = () => useContext(MetaContext);

export function MetaProvider({ children }: {children: JSX.Element}): JSX.Element {
    const [version, setVersion] = useState<string>("");

    useInitMeta(setVersion);

    const data: MetaData = {
        version,
    }

    return (
        <>
            <MetaContext.Provider value={data}>
                {children}
            </MetaContext.Provider>
        </>
    )
}

type MetaData = {
    version: string,
}