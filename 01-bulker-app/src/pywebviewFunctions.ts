import { ReaderType } from "./components/SettingsComponents/types";
import "./pywebview";
import { Metadata, Response } from "./pywebviewTypes";

/**
 * Retrieves the contents of the reader.
 * @param reader The Reader type
 * @returns The Reader content, which is an Object with a string of any type
 */
export async function getReaderContent(reader: ReaderType): Promise<Record<string, any>>{
    const res: Record<string, string> = await window.pywebview.api.get_reader_content(reader);

    return res;
}

/**
 * Generates a password. The password can be found in the `content` key of the Response.
 */
export async function generatePassword(): Promise<string>{
    const res: Response = await window.pywebview.api.generate_password();

    const password: string = res["content"] as string;

    return password;
}

/**
 * Retrieves the metadata of the program.
 * @returns Metadata object
 */
export async function getMetadata(): Promise<Metadata>{
    const meta: Metadata = await window.pywebview.api.get_metadata();

    return meta;
}

/**
 * Recursively updates a key with a value in a Reader
 * @param reader The Reader type to target
 * @param key The key which value is being updated
 * @param value Any value for the key
 * @param parent Ensures the update occurs in the parent key, only required if multiple keys exist in different nest levels
 */
export async function updateSetting(key: string, value: any, parent?: string): Promise<Response>{
    const res: Response = await window.pywebview.api.update_setting(key, value, parent);

    return res;
}

/**
 * Checks if an update is needed for the program
 * @returns Response Promise
 */
export async function checkVersion(): Promise<Response>{
    return await window.pywebview.api.check_version();
}

/**
 * Runs the updater. This will exit the current program if successful.
 * @returns Response Promise if successful
 */
export async function runUpdater(): Promise<Response>{
    const res: Response = await window.pywebview.api.run_updater();

    return res;
}