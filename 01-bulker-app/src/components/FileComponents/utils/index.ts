import React from 'react';
import { toastError, toastSuccess } from '../../../toastUtils.ts';
import '../../../pywebview.ts';
import { UploadedFilesProps, FileStatus, GenerateCSVProps, FileType } from './types.ts';
import { Response } from '../../../pywebviewTypes.ts';
import { generateId } from "../../../utils.ts"; 

//** Updates the uploaded files state with the event file from the input element. */
export function onFileChange(
    event: React.SyntheticEvent<HTMLInputElement>, 
    setUploadedFiles: React.Dispatch<React.SetStateAction<Array<UploadedFilesProps>>>){
        const id: string = Date.now().toString();
        const file: File|undefined = event.currentTarget.files?.[0];
        
        // some weird thing with input elements. if i recall this was an issue in my last project too.
        event.currentTarget.value = "";

        if(!file) return;

        const res: Record<string, string> = validateFile(file);

        if(res.status == "error"){
            toastError(res.message);

            return;
        }

        setUploadedFiles(prev => [
            ...prev, 
            {
                id: id, 
                name: file.name, 
                file: file, 
                status: "none", 
                fileType: res.fileType as FileType,
                errMsg: undefined, // this gets updated once the backend call completes
            }
        ]);
}

//** Reads a file and generates a Base64 string for decoding. */
async function getBase64(file: File): Promise<string | ArrayBuffer | null>{
    return new Promise((resolve, reject) => {
        const reader: FileReader = new FileReader();

        reader.readAsDataURL(file);
        reader.onload = () => {
            resolve(reader.result);
        };
        reader.onerror = (error) => {
            reject(error);
        }
    })
}

//** Upload the file state and and generate the CSV for Azure. */
export async function uploadFile(
    event: React.SyntheticEvent<HTMLFormElement>,
    fileArr: Array<UploadedFilesProps>,
    setFileArr: React.Dispatch<React.SetStateAction<Array<UploadedFilesProps>>>,
    flattenCsv: boolean = false): Promise<boolean>{
    event.preventDefault();

    // helper function for handling errors on a file
    const handleFileError = (msg: string, fileId: string) => {
        const file: UploadedFilesProps = fileArr.filter(files => files.id == fileId)[0];
        toastError(`Failed file ${file.name}`);

        setFileArr(prev => prev.map(fileObj => {
            if(fileObj.id == fileId){
                return {...fileObj, status: "error", msg: msg};
            }

            return fileObj;
        }))
    }

    // by default it will assume true, it is modified inside the csv generation call.
    let uploadSuccess: boolean = true;
    if(fileArr.length == 0){
        toastError("No files were submitted.");
        return true;
    }

    const csvResponseArr: Array<GenerateCSVProps> = [];

    // setting up the b64 strings to send to the backend.
    for(const file of fileArr){
        const res: Record<string, string> = validateFile(file.file);

        if(res.status == "error"){
            handleFileError(res.message, file.id);
            
            continue;
        }

        try{
            const b64: string|ArrayBuffer|null = await getBase64(file.file);
            
            csvResponseArr.push({fileName: file.name, b64: b64 as string, id: file.id})
        }catch (error){
            console.log(error);

            handleFileError(`An error occurred while reading ${file.name}`, file.id);
        } 
    }

    // used with flattenCsv flag, it will be regenerated if false.
    let uploadId: string = generateId();
    for(const csvObj of csvResponseArr){
        let status: FileStatus = "success";
        let resMessage: string = "";

        try{
            const res: Response = await window.pywebview.api.generate_azure_csv(csvObj, uploadId);
            
            if(res["status"] == "error"){
                status = "error";

                uploadSuccess = false;
            }

            resMessage = res.message;
        }catch(error){
            // toast error here due to it being a critical error.
            if(error instanceof Error){
                toastError(error.message);
                status = "error";

                resMessage = error.message;
                uploadSuccess = false;
            }
        }

        setFileArr(prev => prev.map(p => {
            if(p.id == csvObj.id){
                return {...p, status: status, msg: resMessage};
            } 
            
            return p;
        }));

        if(!flattenCsv){
            uploadId = generateId();
        }
    }

    return uploadSuccess;
}

export function onDragDrop(event: React.DragEvent, 
    setUploadedFiles: React.Dispatch<React.SetStateAction<Array<UploadedFilesProps>>>
): void{
    event.preventDefault();
    const id: string = Date.now().toString();
    const file: File|null = event.dataTransfer?.files[0] ?? null;

    if(!file) return;

    const res: Record<string, string> = validateFile(file);

    if(res.status == "error"){
        toastError(res.message);
        return;
    }

    setUploadedFiles(prev => [
        ...prev, 
        {
            id: id, 
            name: file.name, 
            file: file, 
            status: "none",
            fileType: res.fileType as FileType
        }
    ]);
}

//** Removes an object from the uploaded files state on a matching ID. */
export function deleteFileEntry(
    fileID: string,
    setUploadedFiles: React.Dispatch<React.SetStateAction<Array<UploadedFilesProps>>>,
): void{
    setUploadedFiles(prev => prev.filter(ele => {
        return ele.id != fileID;
    }));
}

/**
 * Validates a File object for file uploads
 * @param file A File object
 */
function validateFile(file: File): Record<string, string>{
    const res: Record<string, string> = {
        "status": "success", 
        "message": "Valid file",
        "fileType": "",
    };

    const fileName: string = file.name;
    const fileExt: string = fileName.split(".").at(-1)?.toLowerCase() || "invalid";

    const validExtenions: Set<string> = new Set([
        "xlsx", 
        "csv"
    ]);

    if(!validExtenions.has(fileExt)){
        res.status = "error";
        res.message = "Only files ending in .csv and .xlsx are accepted.";

        return res;
    }

    res.fileType = fileExt;

    return res;
}