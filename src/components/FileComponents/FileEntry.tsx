import { JSX } from "react";
import { useFileContext } from "../../context/FileContext";
import { UploadedFilesProps } from "./utils/types";
import { deleteFileEntry } from "./utils";
import { FaTrash, FaTimes, FaCheck, FaRegFileExcel, FaRegFileAlt } from "react-icons/fa";

const iconSize: number = 25;

export default function FileEntry({file}: {file: UploadedFilesProps}): JSX.Element{
    const { setUploadedFiles } = useFileContext();

    return (
        <>
            <div className={`px-7 min-h-30 max-h-30 default-shadow rounded-xl w-[90%] flex flex-col items-center border-1 border-gray-300
            ${file.status == "none" ? "" : file.status == "success" ? "bg-green-200/90" : "bg-red-200/90"}`}>
                <div className="flex items-center justify-between w-full mt-5">
                    <div className="flex items-center gap-2 text-ellipsis" title={file.name}>
                        {   
                            file.fileType == "xlsx" ? 
                            <FaRegFileExcel color="#519E3E" size={iconSize} />
                            : file.fileType == "csv" &&
                            <FaRegFileAlt color="#314f1b" size={iconSize} />
                        }
                        <span className="font-medium">
                            {file.name}
                        </span>
                    </div>
                    <div className="flex justify-center items-center">
                        <span 
                        onClick={() => deleteFileEntry(file.id, setUploadedFiles)}
                        className="hover:bg-gray-400 p-2 rounded-xl">   
                            <FaTrash />
                        </span>
                    </div>
                </div>
                <div className="text-gray-600 w-full text-sm">
                    {file.msg != undefined && file.msg}
                </div>
            </div>
        </>
    )
}