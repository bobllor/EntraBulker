import { uploadFile } from "./utils"; 
import { useFileContext } from "../../context/FileContext";
import Button from "../ui/Button"
import React from "react";
import FileEntry from "./FileEntry";
import { useSettingsContext } from "../../context/SettingsContext";

const widthStyle = "w-160";

export default function UploadForm({inputFileRef, FileUpload, showDrop}){
    const { uploadedFiles, setUploadedFiles } = useFileContext();
    const { apiSettings, setUpdateSettings } = useSettingsContext();

    return (
        <>
            <div className={`${showDrop && "pointer-events-none opacity-0 z-0"} w-[50%]
            flex flex-col justify-center items-center`}>
                <>
                    {uploadedFiles.length > 0 &&
                    <div className={`flex justify-start ${widthStyle} px-5`}>
                        <FileUpload inputFileRef={inputFileRef} hasUploadedFiles={true}/>
                    </div>
                    }
                    <div className={`border-1 h-90 ${widthStyle} p-3 rounded-xl flex flex-col items-center gap-3
                    ${uploadedFiles != 0 ? "overflow-y-scroll" : "justify-center"}
                    ${!showDrop && "z-2"}`}>
                        {uploadedFiles.length == 0 && <FileUpload inputFileRef={inputFileRef} />}
                        <>
                          {uploadedFiles.map((file, i) => (
                              <React.Fragment key={i}>
                                  <FileEntry file={file} />
                              </React.Fragment>
                          ))}
                        </>
                    </div>
                </>
                <form 
                className={`flex flex-col justify-center items-center gap-3 p-5 ${!showDrop && "z-2"}`}
                onSubmit={(e) => uploadFile(e, uploadedFiles, setUploadedFiles, apiSettings.flatten_csv).then(status => {
                    if(!status){
                        setUpdateSettings(true);
                    }
                })}>
                    <div>
                        <Button text={"Submit"} paddingX={10} paddingY={3} />
                    </div>
                </form>
            </div>
        </>
    )
}