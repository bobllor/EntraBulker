import { uploadFile } from "./utils"; 
import { useFileContext } from "../../context/FileContext";
import Button from "../ui/Button"
import React, { useRef } from "react";
import FileEntry from "./FileEntry";
import { useSettingsContext } from "../../context/SettingsContext";
import { throttler } from "../../utils";

const widthStyle = "w-160";

export default function UploadForm({inputFileRef, FileUpload, showDrop}){
    const { uploadedFiles, setUploadedFiles } = useFileContext();
    const { apiSettings, setUpdateSettings } = useSettingsContext();
    
    const uploadThrottle = useRef(throttler((e, uploadedFiles, setUploadFiles, flatten_csv, setUpdateSettings) => {
        uploadFile(e, uploadedFiles, setUploadFiles, flatten_csv, setUpdateSettings).then((status) => {
            if(!status){
                setUpdateSettings(true);
            }
        });
    }));

    return (
        <>
            <div className={`${showDrop && "z-0"} w-[50%]
            flex flex-col justify-center items-center`}>
                <div className={`flex justify-start ${widthStyle} px-5 
                ${uploadedFiles.length == 0 ? "opacity-0 z-[-1]" : "opacity-100"}`}>
                    <FileUpload inputFileRef={inputFileRef} hasUploadedFiles={true}/>
                </div>
                <div className={`border-1 border-black/50 default-shadow ${widthStyle} p-3 rounded-xl flex flex-col items-center gap-3 overflow-y-scroll ${uploadedFiles == 0 && "justify-center"} ${!showDrop && "z-2"} max-h-90 min-h-90 scroll-style`}>
                    {uploadedFiles.length == 0 && <FileUpload inputFileRef={inputFileRef} />}
                        {uploadedFiles.map((file, i) => (
                            <React.Fragment key={i}>
                                <FileEntry file={file} />
                            </React.Fragment>
                        ))}
                </div>
                <form 
                className={`flex flex-col justify-center items-center gap-3 p-5 ${!showDrop && "z-2"}`}
                onSubmit={(e) => {
                    e.preventDefault();

                    uploadThrottle.current(e, uploadedFiles, setUploadedFiles, apiSettings.flatten_csv, setUpdateSettings);
                }}>
                    <div>
                        <Button text={"Submit"} paddingX={10} paddingY={3} />
                    </div>
                </form>
            </div>
        </>
    )
}