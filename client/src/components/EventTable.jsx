import React from "react";
import BaseTable, {Column} from "react-base-table";

export default function EventTable({events}) {
    return (
        <BaseTable data={events} width={600} height={500}>
            <Column key="hostname" dataKey="hostname" width={100} />
            <Column key="uuid" dataKey="uuid" width={120} />
        </BaseTable>
    )
}
