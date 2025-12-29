import React, { useEffect, useState } from 'react';
import ProgressBar from './components/ProgressBar'
import "./pywebFunctions";
import { checkVersion, clean, downloadZip, isProduction, startMainApp, unzip, update } from './pywebFunctions';
import ProgressText from './components/ProgressText';

const FUNCTIONS = [
  {func: downloadZip, initialText: "Downloading ZIP file"},
  {func: unzip, initialText: "Extracting file contents to temp folder"},
  {func: update, initialText: "Updating application files"},
  {func: clean, initialText: "Removing temp folder"},
  {func: startMainApp, initialText: "Starting application"},
];
const PERCENT = Math.floor(100 / FUNCTIONS.length);
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
  const [failedUpdate, setFailedUpdate] = useState(true);

  // must be initially false otherwise it will run
  const [isProd, setIsProd] = useState(null);

  // used to get production/test environments
  useEffect(() => {
    setTimeout(async () => {
      const prodStatus = await isProduction();

      setIsProd(prodStatus);
      console.log("Initial status:", isProd);
    }, 500)
  }, [])

  useEffect(() => {
    console.log("Final status:", isProd);
    if(isProd){
      setTimeout(async ()=> {
        const res = await checkVersion();

        if(res["content"]){
          run(FUNCTIONS, setProgressText, setFailedUpdate, setInnerProgressBarWidth, PERCENT);
        }else{
          const text = "No update found";
          setProgressText(prev => [{text: text, status: "error"}, ...prev]);
          setFailedUpdate(true);
        }
      }, 600)
    }
  }, [isProd])

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
        {!isProd && isProd != null && 
          <button onClick={
            () => {
              checkVersion().then(res => console.log(res));
              run(FUNCTIONS, setProgressText, setFailedUpdate, setInnerProgressBarWidth, PERCENT);
            }}>
            Test
          </button>
        }
      </div>
    </>
  )
}

/**
 * Starts the updating process.
 * @param {*} arrObj An array of objects holding the `func` updating functions and a `initialText` update text
 * @param {*} setText The setter function for the progress text state
 * @param {*} setFail The setter function for the state tracking if the update fails
 * @param {*} setNumber The setter function to update the progress bar
 * @param {*} add The calculated percent addition derived from the length of `arrObj`, added to the progress bar
 */
async function run(arrObj, setText, setFail, setNumber, add){
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