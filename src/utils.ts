import "./pywebview";

/**
 * Checks if the values of two objects are the same or different. 
 * @param obj - The base object.
 * @param objToCompare - The object for comparison.
 * @returns boolean 
 */
export function compareObjects(baseObj: Object, objToCompare: Object): boolean{
    let hasDifferentValue: boolean = false;

    const baseKeys: string[] = Object.keys(baseObj);

    for(let j = 0; j < baseKeys.length; j++){
        const key: string = baseKeys[j];

        const baseValue = baseObj[key as keyof typeof baseObj];
        const newValue = objToCompare[key as keyof typeof baseObj];

        if(baseValue != newValue){
            hasDifferentValue = true; 
            break;
        }
    }

    return hasDifferentValue;
}

/**
 * A throttler closure.
 * @param func Any function.
 * @param timeout The timeout threshold for resetting the flag. By default it is `500` ms.
 * @returns A wrapper of the given function for throttling.
 */
export function throttler(func: (...args: any) => any | Promise<any>, timeout: number = 500): (...args: any) => void{
    let flag: boolean = false;

    return (...args: any) => {
        if(!flag){
            func(...args);
            flag = true;
            setTimeout(() => {
                flag = false;
            }, timeout)
        }
    }
}

/**
 * 
 * @param func Any function.
 * @param timeout The timeout threshold before executing the function, by default it is `700` ms.
 * @returns A wrapper of the given function for debouncing.
 */
export function debouncer(func: (...any: any) => any | Promise<any>, timeout: number = 700): (...any: any) => void{
    let timer: number | undefined;

    return (...any: any) => {
        clearTimeout(timer);

        timer = setTimeout(() => {
            func(...any);
        }, timeout);
    }
}

/**
 * Generates a random ID.
 * @returns {string} The ID.
 */
export function generateId(): string{
    const id: string = Math.random().toString(16).slice(2);

    return id;
}

/**
 * Checks if the response of the backend call is successful. Requires the response to
 * have the key `status`.
 * @param res - The response object, map, or record.
 * @returns {boolean} - If the response is not successful.
 */
export function checkRes(res: Record<string, string>): boolean{
    return res["status"] == "success";
}