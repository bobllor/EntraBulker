import { useRef, useState } from "react";
import UploadForm from "../components/FileComponents/UploadForm";
import FileUpload from "../components/FileComponents/FileUpload";
import { JSX } from "react";
import DragZone from "../components/FileComponents/DragZone";

export default function Home(): JSX.Element {
  const inputFileRef = useRef(null);
  const [showDrop, setShowDrop] = useState<boolean>(false);

  return (
    <> 
      <div className='h-screen w-screen flex justify-center items-center overflow-hidden relative'>
        <DragZone showDrop={showDrop} setShowDrop={setShowDrop} />
        <UploadForm inputFileRef={inputFileRef} FileUpload={FileUpload} showDrop={showDrop}/>
      </div>
    </>
  )
}