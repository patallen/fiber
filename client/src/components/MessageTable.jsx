import React from "react";

const styles = {
    message: {
        fontSize: "12px",
        padding: "8px",
        borderBottom: "1px solid #f1f1f1",
        textAlign: "left",
    },
    messageBoxHeader: {
        padding: "12px 10px",
        color: "#333333",
        textAlign: "left",
        backgroundColor: "#f8f8f8",
        borderBottom: "1px solid #f1f1f1",
    },
    messageBox: {
        border: "1px solid #eaeaea",
        borderRadius: "3px 0 0 0",
        borderBottom: null,
        borderRight: null,
        position: 'absolute',
        backgroundColor: "white",
        width: '300px',
        height: '300px',
        overflow: 'hidden',
        right: 0,
        bottom: 0,
    }
};

const Message = ({message}) => <div style={styles.message}>{message}</div>;
const MessageBoxHeader = ({children}) => (
    <div style={styles.messageBoxHeader}>
        <span>{children}</span>
        <span className="glyphicon glyphicon-plus" />
    </div>
);

export default function MessageBox({messages}) {
    return (
        <div style={styles.messageBox}>
            <MessageBoxHeader>Messages</MessageBoxHeader>
            {
                messages.map(m => (
                    <Message key={m.uuid} message={m.body} />
                ))
            }
        </div>
    )
}
