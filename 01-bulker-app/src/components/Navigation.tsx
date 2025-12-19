import React, { JSX } from "react";
import { NavigateFunction } from "react-router";
import { useNavigate } from "react-router";
import { useModalContext } from "../context/ModalContext";
import { FormStateProps } from "./FormComponents/manualUtils/types";

export default function Navigation({buttons, formState}: {buttons: Array<MainNavigationProps>, formState: FormStateProps}
    ): JSX.Element{
    let navigate: NavigateFunction = useNavigate();

    const { revealModal } = useModalContext();

    async function clickWrapper(url: string): Promise<void>{
      // FIXME: when its ready to be packaged into an app this has to be changed.
      if(window.location.pathname == url) return;

      // only used if a form has been edited before navigation
      if(formState.state){
        const action: boolean = await revealModal('Changes you made are not saved. Are you sure you want to leave?');

        if(!action){
          return;
        }

        formState.func(false);
      }

      navigate(url);
    }
    
    return (
        <>  
        <div className="flex flex-col gap-1 relative">
            {buttons.map((obj, i) => (
              <React.Fragment key={i}>
                <div className="relative flex justify-center items-center group">
                  <div key={i}
                  onClick={() => clickWrapper(obj.url)}
                  className={`p-4 w-fit flex justify-between items-center rounded-xl bg-gray-300
                  hover:bg-gray-500/60 gap-1 text-center`}>
                    {obj.icon && 
                      <span>
                        {obj.icon}
                      </span>
                    }
                  </div>
                  <div className="absolute translate-x-18 w-20 border border-gray-400 pointer-events-none items-center justify-center
                  hidden group-hover:flex p-2 rounded-xl default-shadow bg-gray-300">
                    {obj.label}
                  </div>
                </div>
              </React.Fragment>
            ))}
          </div>
        </>
    )
}

type MainNavigationProps = {
  label: string,
  url: string,
  icon?: JSX.Element,
}