import React from "react";
import BaseTable, {Column} from "react-base-table";
import 'react-base-table/styles.css'


export default function TaskTable({tasks, width, height}) {
    return (
        <BaseTable rowKey="uuid" data={tasks} headerHeight={40} rowHeight={36} width={width} height={height}>
            <Column key="uuid" dataKey="uuid" title="UUID" width={200} />
            <Column key="name" dataKey="name" title="Name" width={300} />
            <Column key="state" dataKey="state" title="State" width={140} />
            <Column key="runtime" dataGetter={({rowData}) => {
                if (rowData.runtime !== undefined) {
                    return rowData.runtime.toFixed(2) + " seconds"
                }
            }} title="Runtime" width={140} />
        </BaseTable>
    )
}
