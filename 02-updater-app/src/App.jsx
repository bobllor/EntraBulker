import { useEffect, useState } from 'react';
import './App.css'
import ProgressBar from './components/ProgressBar'

const functions = [];
const funcLength = functions.length;

export default function App() {
  const [innerProgressBarWidth, setInnerProgressBarWidth] = useState(1);

  useEffect(() => {
    // all functions returns a Response

  }, [])

  return (
    <>
      <div className="w-screen h-screen flex flex-col justify-end items-center">
        <ProgressBar innerProgressBarWidth={innerProgressBarWidth} /> 
        <button onClick={() => setInnerProgressBarWidth(prev => prev+20)}>Test button</button>
      </div>
    </>
  )
}