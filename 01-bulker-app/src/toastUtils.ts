import { toast, ToastPosition } from "react-toastify";
import { Response } from "./pywebviewTypes";

const POSITION: ToastPosition = "top-right"

export function toaster(msg: string, type: "error" | "info" | "success" | "warning", duration: number = 3000): void{
    toast(
        msg,
        {
            position: POSITION,
            type: type,
            closeOnClick: true, 
            pauseOnHover: false,
            pauseOnFocusLoss: false,
            autoClose: duration,
        }
    )
}

/**
 * Takes a response and automatically toasts a successful or error notification. It
 * will use the message of the Response as its value.
 * @param response The Response of the pywebview call
 * @param duration The duration the toast will stay on screen, by default it is 3000
 */
export function toastResponse(response: Response, duration: number = 3000): void{
    toast(
        response.message,
        {
            position: POSITION,
            type: response.status,
            closeOnClick: true, 
            pauseOnHover: false,
            pauseOnFocusLoss: false,
            autoClose: duration,
        },
    );
}

export function toastSuccess(msg: string, duration: number = 3000): void{
    toast(
        msg,
        {
            position: POSITION,
            type: "success",
            closeOnClick: true, 
            pauseOnHover: false,
            pauseOnFocusLoss: false,
            autoClose: duration,
        }
    )
}

export function toastError(msg: string, duration: number = 3000){
    toast(
        msg,
        {
            position: POSITION,
            type: "error",
            closeOnClick: true, 
            pauseOnHover: false,
            pauseOnFocusLoss: false,
            autoClose: duration,
        }
    )
}