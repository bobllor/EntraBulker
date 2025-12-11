export type UploadedFilesProps = {
    id: string,
    name: string,
    file: File,
    status: FileStatus,
    fileType: FileType,
    msg?: string,
}

export type FileStatus = "error" | "success" | "none"
export type FileType = "xlsx" | "csv";

export type GenerateCSVProps = {
    b64: string,
    fileName: string,
    id: string,
}