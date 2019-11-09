import React from "react";

export const TaskStateBadge = ({state}) => {
    const color = ({
        'STARTED': ['#F8F8F8', '#555555'],
        'RECEIVED': ['white', 'black'],
        'REVOKED': ['white', 'orange'],
        'SUCCESS': ['white', 'green'],
        'FAILED': ['white', 'red'],
    })[state];
    return <Badge
        borderColor={color[1]}
        backgroundColor={color[0]}
        color={color[1]}>
          {state.toUpperCase()}
    </Badge>
};

export const StatusBadge = ({online}) => {
    const text = online ? "Online" : "Offline";
    const color = online ? "#1daf1d" : "red";
    return <Badge color="white" borderColor="none" backgroundColor={color}>{text}</Badge>
};

function Badge({children, borderColor="black", padding="2px 4px", color="black", backgroundColor="white"}) {
    return <span style={{
        border: `1px solid ${borderColor}`,
        padding,
        backgroundColor,
        color,
        display: "flex",
        alignItems: "center",
        borderSize: "1px",
        fontSize: "11px",
        borderRadius: '4px'
    }}>{children}</span>
}

