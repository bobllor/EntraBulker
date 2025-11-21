import { JSX, useEffect, useRef, useState } from "react";
import { useFileContext } from "../../context/FileContext";
import { UploadedFilesProps } from "./utils/types";
import { deleteFileEntry } from "./utils";
import { FaTrash } from "react-icons/fa";

export default function FileEntry({file}: {file: UploadedFilesProps}): JSX.Element{
    const { setUploadedFiles } = useFileContext();

    const divRef = useRef<HTMLDivElement|null>(null);
    const spanRef = useRef<HTMLSpanElement|null>(null);
    const [scrollText, setScrollText] = useState<boolean>(false);

    useEffect(() => {
        if(!divRef.current || !spanRef.current) return;

        const div: HTMLDivElement = divRef.current!;
        const divSize: number = div.offsetWidth;

        const span: HTMLSpanElement = spanRef.current!;
        const spanSize: number = span.scrollWidth;
        
        if(spanSize > divSize){
            setScrollText(true);

            div.addEventListener("mouseenter", () => scrollHover(spanSize, div));
            div.addEventListener("mouseleave", () => scrollHover(-spanSize, div));
        }

        return () => {
            div.removeEventListener("mouseenter", () => scrollHover(spanSize, div));
            div.removeEventListener("mouseleave", () => scrollHover(-spanSize, div));
        }
    }, [])

    return (
        <>
            <div className={`px-5 py-2 default-shadow rounded-xl w-[90%] flex justify-between
                ${file.status == "none" ? "" : file.status == "success" ? "bg-green-300" : "bg-red-300"}`}>
                <div
                title={file.name}
                ref={divRef}
                className="flex p-2 w-[60%] bg-gray-400/20 text-nowrap default-shadow rounded-xl overflow-x-hidden">
                    <span
                    className="text-center w-full"
                    ref={spanRef}
                    >{file.name}</span>
                </div>
                <div className="flex justify-center items-center">
                    <span 
                    onClick={() => deleteFileEntry(file.id, setUploadedFiles)}
                    className="hover:bg-gray-400 p-2 rounded-xl">   
                        <FaTrash />
                    </span>
                </div>
            </div>
        </>
    )
}

function scrollHover(scrollAmount: number, element: HTMLElement): void{
    element.scroll({
        left: scrollAmount,
        behavior: "smooth",
    })
}