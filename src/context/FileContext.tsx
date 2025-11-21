import { JSX } from "react";
import { useContext, createContext, useState } from "react";
import { UploadedFilesProps } from "../components/FileComponents/utils/types";

const FileContext = createContext<FileData>({
    uploadedFiles: [],
    setUploadedFiles: () => {}
});

export const useFileContext = () => useContext(FileContext);

export function FileProvider({ children }: {children: JSX.Element}): JSX.Element {
    const [uploadedFiles, setUploadedFiles] = useState<Array<UploadedFilesProps>>([]);

    const data: FileData = {
        uploadedFiles,
        setUploadedFiles
    }

    return (
        <>
            <FileContext.Provider value={data}>
                {children}
            </FileContext.Provider>
        </>
    )
}

type FileData = {
    uploadedFiles: Array<UploadedFilesProps>,
    setUploadedFiles: React.Dispatch<React.SetStateAction<Array<UploadedFilesProps>>>,
}