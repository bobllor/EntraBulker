import { JSX } from "react";
import EditCell from "./EditCell";
import { ManualData } from "./manualUtils/types";

export default function TableData({id, data, edit, maxLength, manData, select}: TableDataProps): JSX.Element{
    return (
        <>
            <td
            onClick={() => edit.editCell == "" && select.setSelectedCell(id + data)}
            onDoubleClick={() => {
                select.setSelectedCell(id + data);
                edit.setEditCell(id + data);
            }}
            className={`px-4 py-2 text-center text-wrap min-w-50 max-w-50 overflow-x-hidden
            ${select.selectedCell == id + data 
                ? "bg-gray-400 outline-blue-400/40 outline-1 z-1"
                : edit.editCell == "" && "hover:bg-gray-400/40"
            }`}
            title={data.length > maxLength ? data : ""}>
                {data.length > maxLength ? data.slice(0, 20) + "..." : data}
                {id + data == edit.editCell && 
                <EditCell id={id} stringVal={data} setEditCell={edit.setEditCell} manData={manData} 
                    checkEmpty={edit.checkEmpty ? edit.checkEmpty : false}/>
                }
            </td>
        </>
    )
}

type TableDataProps = {
    id: string,
    data: string,
    maxLength: number,
    edit: {
        editCell: string,
        setEditCell: React.Dispatch<React.SetStateAction<string>>,
        checkEmpty?: boolean,
    },
    manData: {
        manualData: Array<ManualData>
        setManualData: React.Dispatch<React.SetStateAction<Array<ManualData>>>
    }
    select: {
        selectedCell: string,
        setSelectedCell: React.Dispatch<React.SetStateAction<string>>
    }
}