import { JSX } from "react";
import { NavigateFunction } from "react-router";
import { useNavigate } from "react-router";
import { useModalContext } from "../context/ModalContext";
import { FormStateProps } from "./FormComponents/manualUtils/types";
import { FaHammer, FaHome } from "react-icons/fa";

const buttons: Array<MainNavigationProps> = [
    {label: 'Home', url: '/', icon: <FaHome size={20}/>},
    {label: 'Custom', url: '/custom', icon: <FaHammer size={20} />}
]

export default function Navigation({formState}: {formState: FormStateProps}
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
            {buttons.map((obj, i) => (
              <div key={i}
              onClick={() => clickWrapper(obj.url)}
              className={`p-2 w-25 flex justify-between items-center rounded-xl bg-gray-300
              hover:bg-gray-500/60 gap-1 text-center`}>
                {obj.icon && 
                  <span>
                    {obj.icon}
                  </span>
                }
                <div className="flex justify-start items-center w-full select-none">
                  {obj.label}
                </div>
              </div>
            ))}
        </>
    )
}

type MainNavigationProps = {
  label: string,
  url: string,
  icon?: JSX.Element,
}