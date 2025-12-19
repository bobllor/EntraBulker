import React, { useEffect } from "react";
import { NavigateFunction, useLocation, useNavigate } from "react-router";
import { checkVersion, runUpdater } from "./pywebviewFunctions";
import { Response } from "./pywebviewTypes";

/**
 * Dismisses a component by using an HTML element for listening and
 * the setter state function of the component.
 * This is only used for components based off of routes and will auto navigate
 * to the root route.
 * 
 * @param element - Any HTMLElement, if it is null then this will return void.
 * @param setShowComponent - The set state function, it must be a boolean.
 */
export function useDismissRoute(
    targetRef: React.RefObject<HTMLElement|null>,
    setShowComponent: React.Dispatch<React.SetStateAction<boolean>>,
): void{
    const navigate: NavigateFunction = useNavigate()
    let location = useLocation();
    useEffect(() => {
        const element = targetRef.current;
        if(!element) return;

        const dismiss = () => {
            navigate(location.state?.previousLocation || "/");
            setShowComponent(false);
        }
        const onClick = (e: MouseEvent) => {
            if(e.currentTarget == element){
                dismiss();
            }
        }

        const onKeyDown = (e: KeyboardEvent) => {
            switch(e.key){
                case "Escape":
                    dismiss();
                default:
                    return;
            }
        }

        element.addEventListener("click", onClick);
        document.addEventListener("keydown", onKeyDown);

        return () => {
            element.removeEventListener("click", onClick);
            document.removeEventListener("keydown", onKeyDown);
        }
    }, [])
}

/**
 * Disables certain shortcut keys on the application.
 */
export function useDisableShortcuts(){
    useEffect(() => {
        window.addEventListener("keydown", (event) => {
            const keyValue: string = event.key;

            const allowedKeys = new Set<string>([
                "Backspace", "a", "c", "v", 
                "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown",
            ]);
            
            if(event.ctrlKey){
                if(!allowedKeys.has(keyValue)){
                    event.preventDefault();
                }
            }
        })
    }, [])
}

/**
 * Disables the context menu.
 */
export function useDisableContext(){
    useEffect(() => {
        window.addEventListener("contextmenu", (event) => {
            event.preventDefault();
        })
    }, [])
}

/**
 * Checks an update for the program. This is only called once on load, until the program restart.
 */
export function useCheckUpdate(revealModal: (text: string) => Promise<boolean>, text: string){
    useEffect(() => {
        setTimeout(async () => {
            let res: Response = await checkVersion();
            
            // errors will be ignored completely.
            if(res.status == "success"){
                const hasUpdate: boolean = res["has_update"];
                
                if(!hasUpdate){
                    const modalAction: boolean = await revealModal(text);
                    
                    if(modalAction){
                        res = await runUpdater();

                        console.log(res);
                    }
                }
            }
        }, 2000)
    }, [])
}