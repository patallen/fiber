import React from "react";
import BaseTable, {Column} from "react-base-table";
import 'react-base-table/styles.css'


export default function EventTable({events}) {
    console.log("EVENTS", events);
    return (
        <BaseTable rowKey="event_id" data={events} headerHeight={40} rowHeight={36} width={900} height={500}>
            <Column key="hostname" dataKey="hostname" title="Hostname" width={130} />
            <Column key="uuid" dataKey="uuid" title="Task UUID" width={300} />
            <Column key="type" dataKey="type" title="Event Type" width={100} />
            <Column key="timestamp" width={200} title="Timestamp" dataGetter={({rowData}) => new Date(rowData.timestamp)} />
            <Column key="name" dataKey="name" title="Task Name" width={100} />
        </BaseTable>
    )
}
