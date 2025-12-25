import { Routes, Route, useLocation, useNavigate } from "react-router";
import { useEffect, useState } from "react";
import Navigation from "./components/Navigation";
import Custom from "./routes/Custom";
import Home from "./routes/Home";
import Settings from "./routes/Settings";
import Modal from "./components/Modal";
import { useModalContext } from "./context/ModalContext";
import { ToastContainer } from "react-toastify";
import General from "./components/SettingsComponents/OptionsComponents/General";
import HeadersMapping from "./components/SettingsComponents/OptionsComponents/HeadersMapping";
import OpcoMapping from "./components/SettingsComponents/OptionsComponents/OpcoMapping";
import TextForm from "./components/SettingsComponents/OptionsComponents/TextForm";
import Password from "./components/SettingsComponents/OptionsComponents/Password";
import { useCheckUpdate, useDisableContext, useDisableShortcuts } from "./hooks";
import { useMetaContext } from "./context/MetaContext";
import { FaHome, FaHammer, FaCog } from "react-icons/fa";

const fullPageStyle = 'h-screen w-screen flex flex-col justify-center items-center overflow-hidden relative p-3'
const navigationButtons = [
    {label: 'Home', url: '/', icon: <FaHome size={20} />},
    {label: 'Custom', url: '/custom', icon: <FaHammer size={20} />}
]

export default function App() {
  // used for buttons and the manual form for the unload.
  const [formEdited, setFormEdited] = useState(false);
  
  const [showSetting, setShowSetting] = useState(false);

  let location = useLocation();
  const navigate = useNavigate();

  const { showModal, revealModal } = useModalContext();
  const { version } = useMetaContext();

  useEffect(() => {
    if(location.pathname.includes("settings")){
      setShowSetting(true);
    }
  }, [location])

  useDisableShortcuts();
  useDisableContext();
  useCheckUpdate(revealModal, "An update has been found. Would you like to start the update?");

  return (
    <> 
      <div 
      onDragOver={e => e.preventDefault()}
      onDrop={e => e.preventDefault()}
      className={fullPageStyle}>
        <ToastContainer />
        {showModal && <Modal />}
        {location.state?.previousLocation &&
          <Routes>
            <Route path="settings" element={<Settings setShowSetting={setShowSetting} />}> 
              <Route index element={<General />} />
              <Route path="headers-mapping" element={<HeadersMapping />} />
              <Route path="opco-mapping" element={<OpcoMapping />} />
              <Route path="template" element={<TextForm />} />
              <Route path="password" element={<Password />} />
            </Route>
          </Routes>
        }
        <div className="absolute left-0 z-2 flex flex-col justify-center items-center gap-2">
          <div className="h-screen w-20 flex flex-col items-center gap-1 py-10 justify-between">
            <Navigation buttons={navigationButtons} formState={{state: formEdited, func: setFormEdited}} />
            <div
            onClick={() => navigate("/settings", {replace: true, state: {previousLocation: location}})}
            className={`flex justify-center items-center rounded-2xl p-4 z-3 bg-gray-300 
            hover:bg-gray-500/60 ${showSetting && "pointer-events-none"} group outline-0`}>
                <FaCog size={20} />
                <div className="absolute translate-x-18 w-20 border border-gray-400 pointer-events-none items-center justify-center
                  hidden group-hover:flex p-2 rounded-xl default-shadow bg-gray-300">
                  Settings
                </div>
            </div>
          </div>
        </div>
        <Routes location={location.state?.previousLocation || location}>
            <Route path='/' element={<Home />} />
            <Route path='custom' element={<Custom style={fullPageStyle} 
              formState={{state: formEdited, func: setFormEdited}}/>} />
            <Route path="settings" element={<Settings setShowSetting={setShowSetting} />} />
        </Routes>
        <div className="w-full flex justify-end items-center px-5 fixed bottom-0">
          {version}
        </div>
      </div>
    </>
  )
}
