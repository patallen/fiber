import React from "react";
import BaseTable, {Column} from "react-base-table";
import 'react-base-table/styles.css'
import './styles.task-table.css';

import {TaskStateBadge} from "../components/Badge"

export default function TaskTable({tasks, width, height}) {
    return (
        <BaseTable align="center" rowKey="uuid" data={tasks} headerHeight={40} rowHeight={36} width={width}
                   height={height}>
            <Column key="uuid" dataKey="uuid" title="UUID" width={300}/>
            <Column key="name" dataKey="name" title="Name" width={300}/>
            <Column key="state" dataGetter={({rowData}) => {
                const taskState = rowData.state || "RECEIVED";
                return <TaskStateBadge state={taskState} backgroundColor="blue">{taskState}</TaskStateBadge>
            }} title="State" width={140}/>
            <Column key="runtime" dataGetter={({rowData}) => {
                // Fine for now but the time is not actively incrementing
                if (rowData.runtime) {
                    if (rowData.runtime.toFixed(3) >= 1) {
                        return rowData.runtime.toFixed(2) + ' s'
                     }
                    return rowData.runtime.toFixed(3) * 1000 + " ms"
                }
                 else {
                    return ((new Date().getTime() - (rowData.created_at * 1000)).toFixed(3)) + " ms"
                }
            }} title="Runtime" width={140} />
            <Column key="created_at" dataGetter={({rowData}) => new Date(rowData.created_at * 1000).toLocaleString({
                dateStyle: "short",
                timeStyle: "medium"
            })} title="Created" width={300} />
        </BaseTable>
    )
}
