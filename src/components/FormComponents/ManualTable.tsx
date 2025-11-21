import { JSX, useState } from "react";
import { tableHeaders } from "./manualUtils/vars";
import { ManualData, SelectStateProps } from "./manualUtils/types";
import TableData from "./TableData";
import { FaTrash } from "react-icons/fa";

export default function ManualTable({manualData, setManualData, select}: 
    ManualTableProps): JSX.Element{
    
    // uses the ID of manualData to display the cell
    const [editCell, setEditCell] = useState<string>('');

    return (
        <>
            <table
            className="w-full text-left">
                <thead className="uppercase bg-gray-400 border-1 border-gray-400">
                    <tr>
                        {tableHeaders.map((header, i) => (
                            <th key={i}
                            className="px-4 py-1 w-25 text-center">{header}</th>
                        ))}
                        <th className="w-3"></th>
                    </tr>
                </thead>
                <tbody>
                    {manualData.map((obj, i) => (
                        <tr
                        className={`border-1 border-gray-400 
                            ${editCell == "" && "hover:bg-blue-400/40"} ${(i + 1) % 2 == 0 && 'bg-gray-200'}`} 
                        key={i}>
                            <TableData 
                            id={obj.name! + obj.id}
                            data={obj.name!}
                            maxLength={16}
                            edit={{editCell: editCell, setEditCell: setEditCell}} 
                            manData={{manualData: manualData, setManualData: setManualData}}
                            select={{selectedCell: select.selectedCell, setSelectedCell: select.setSelectedCell}} />
                            <TableData 
                            id={obj.opco! + obj.id}
                            data={obj.opco!}
                            maxLength={20}
                            edit={{editCell: editCell, setEditCell: setEditCell}} 
                            manData={{manualData: manualData, setManualData: setManualData}}
                            select={{selectedCell: select.selectedCell, setSelectedCell: select.setSelectedCell}} />
                            <td
                            className="px-1">
                                <span 
                                onClick={() => setManualData(prev => prev.filter((_, id) => {return id != i;}))
                                }
                                className="flex justify-center items-center hover:bg-gray-400 rounded-xl py-2 px-1">  
                                    <FaTrash />
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    )
}

type ManualTableProps = {
    manualData: ManualData[], 
    setManualData: React.Dispatch<React.SetStateAction<Array<ManualData>>>,
    select: SelectStateProps
}