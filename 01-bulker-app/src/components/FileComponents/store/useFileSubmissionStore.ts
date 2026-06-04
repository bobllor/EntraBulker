import { create } from "zustand";

type FileSubmissionStore = {
    /**
     * The state of the submission, it is either false or true. If it is
     * true, then the submission is current in progress.
     */
    processing: boolean,
    /**
     * Sets the processing status.
     * @param status The boolean status
     * @returns 
     */
    setProcessing: (status: boolean) => void
}

export const useFileSubmissionStore = create<FileSubmissionStore>((set) => ({
    processing: false,
    setProcessing: (status) => set(prev => ({...prev, processing: status})),
}));