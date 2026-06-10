import { JSX, useState } from "react";
import { useProcessingErrorStore } from "../components/FileComponents/store/useProcessingErrorStore";
import { FaAngleDown, FaAngleRight } from "react-icons/fa";

const ICON_SIZE = 15;

/**
 * Component used for displaying error logs during file parsing/user creation/processing
 * errors. This should not be used to display internal logging but rather is client-facing.
 * 
 * @returns The log page JSX element
 */
export default function ProcessingLog(): JSX.Element{
    const processErrors = useProcessingErrorStore(st => st.errors);

    const [revealLogs, setRevealLogs] = useState(new Set<string>());

    const onClickRevealLog = (logName: string) => {
        if(revealLogs.has(logName)){
            setRevealLogs(prev => {
                const newSet = new Set<string>();

                prev.forEach(v => {
                    if(v != logName){
                        newSet.add(v);
                    }
                })

                return newSet;
            })
        }else{
            setRevealLogs(prev => (new Set<string>([...prev, logName])));
        }
    }
    

    return (
        <div className="default-shadow border border-black/40 rounded-2xl h-[80%] w-[70%] p-2">
            <div className="default-shadow border border-black/40 h-full rounded-xl p-2">
                <h1 className="text-xl">
                    Processing Logs
                </h1>
                <hr />
                <div className="text-wrap overflow-y-auto h-[95%] py-2">
                    {processErrors.map(obj => (
                    <div key={obj.id}>
                        <div 
                        className="flex items-center max-w-full text-sm">
                            <div
                            onClick={() => onClickRevealLog(obj.id)}>
                                {!revealLogs.has(obj.id)
                                ? <FaAngleRight size={ICON_SIZE} />
                                : <FaAngleDown size={ICON_SIZE} />
                                }
                            </div>
                            <p
                            onClick={() => onClickRevealLog(obj.id)}
                            title={`${obj.fileName} (${obj.graphError.failed_users_count}/${obj.graphError.total_users_count} users failed)`}
                            className="overflow-hidden text-ellipsis whitespace-nowrap block px-1 hover:bg-gray-500/50 rounded-2xl">
                                {obj.graphError.timestamp} | <strong>{obj.fileName}</strong>
                            </p> 
                        </div>
                        {revealLogs.has(obj.id) && 
                        <div>
                            <ul className="list-disc list-inside">
                                {obj.graphError.failed_users.map((failedObj, i) => (
                                <li 
                                className="px-2 select-text text-sm"
                                key={i}>
                                    {failedObj.name}: {failedObj.error}
                                </li>
                                ))}
                            </ul>
                        </div>
                        }
                    </div>
                    ))}
                </div>
            </div>
        </div>
    );
}