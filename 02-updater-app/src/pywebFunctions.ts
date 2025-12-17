import "../../01-bulker-app/src/pywebview";
import {Response} from "../../01-bulker-app/src/pywebviewTypes";

/**
 * Downloads the ZIP file to the temp folder
 * @returns Response Promise
 */
export async function downloadZip(): Promise<Response>{
    return await window.pywebview.api.download_zip();
}

/**
 * Extracts all the files from the ZIP file
 * @returns Response Promise
 */
export async function unzip(): Promise<Response>{
    return await window.pywebview.api.unzip();
}

/**
 * Removes the all files from temp
 * @returns Response Promise
 */
export async function clean(): Promise<Response>{
    return await window.pywebview.api.clean();
}

/**
 * Begins the file updating process
 * @returns Response Promise
 */
export async function update(): Promise<Response>{
    return await window.pywebview.api.update();
}

/**
 * Starts the main application, this exits the updater
 * @returns Response Promise
 */
export async function startMainApp(): Promise<Response>{
    // this closes out the window once called and exits the updater.
    // still returning to prevent potential errors, but it shouldnt matter in the end.
    await window.pywebview.api.start_main_app();

    return new Promise((resolve) => resolve({"message": "Exiting updater, starting application", "status": "success"}));
}