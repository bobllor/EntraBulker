import { toast, ToastPosition } from "react-toastify";

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