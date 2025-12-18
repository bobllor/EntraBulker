import React, { useEffect, useState } from 'react';
import './App.css'
import ProgressBar from './components/ProgressBar'
import "./pywebFunctions";
import { clean, downloadZip, startMainApp, unzip, update } from './pywebFunctions';
import ProgressText from './components/ProgressText';

// TODO: once ready, remove the comments
const FUNCTIONS = [
  {func: downloadZip, initialText: "Downloading ZIP file"},
  {func: unzip, initialText: "Extracting file contents to temp folder"},
  {func: update, initialText: "Updating application files"},
  {func: clean, initialText: "Removing temp folder"},
  {func: startMainApp, initialText: "Starting application"},
];
const PERCENT = Math.floor(100 / FUNCTIONS.length);
const IS_TEST = false;
const TEXT_COLORS = {
  0: "text-black",
  1: "text-black/80",
  2: "text-black/60",
  3: "text-black/40",
  4: "text-black/20",
}

export default function App() {
  const [innerProgressBarWidth, setInnerProgressBarWidth] = useState(0);
  const [progressText, setProgressText] = useState([{text: "Starting updating process...", status: "success"}]);
  const [failedUpdate, setFailedUpdate] = useState(false);

  useEffect(() => {
    // timeout is required due to pywebview still loading initially. i think.
    if(!IS_TEST){
      setTimeout(() => {
        startRun(FUNCTIONS, setProgressText, setFailedUpdate, setInnerProgressBarWidth, PERCENT);
      }, 600)
    }
  }, [])

  return (
    <>
      <div className="w-screen h-screen flex flex-col justify-end items-center gap-1 py-3">
        <div className="flex flex-col-reverse w-full h-full text-wrap justify-start">
          {
            progressText.slice(0, 5).map((obj, i) => (
              <React.Fragment key={i}>
                <ProgressText text={obj.text} 
                textColor={
                  obj.status == "success" ? `${TEXT_COLORS[i]}` : "text-red-500"} />
              </React.Fragment>
            ))
          }
        </div>
        <ProgressBar innerProgressBarWidth={innerProgressBarWidth} failed={failedUpdate} /> 
        {IS_TEST && <button onClick={() => startRun(FUNCTIONS, setProgressText, setFailedUpdate, setInnerProgressBarWidth, PERCENT)}>Test</button>}
      </div>
    </>
  )
}

async function startRun(arrObj, setText, setFail, setNumber, add){
  const errorMsg = "ERROR: Failed to update";
  let failedUpdate = false;

  for(const obj of arrObj){
    setText(prev => [{text: obj.initialText, status: "success"}, ...prev]);
    const res = await obj.func();
    
    if(res.status == "success"){
      setText(prev => [{text: res.message, status: "success"}, ...prev]);
      setNumber(prev => prev + add);
    }else{
      setText(prev => [{text: res.message, status: "error"}, ...prev]);
      // keeping the actual restart error message black, red is where it failed.
      setText(prev => [{text: errorMsg, status: "success"}, ...prev]);
      failedUpdate = true;
      setFail(true);
      break;
    }
  }

  const successMsg = "Update successfully completed";
  if(!failedUpdate){
    setText(prev => [{text: successMsg, status: "success"}, ...prev])
  }
}