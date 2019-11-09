import React, {useState} from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'

const styles = {
    message: {
        fontSize: "12px",
        padding: "8px",
        borderBottom: "1px solid #f1f1f1",
        textAlign: "left",
    },
    messageBoxHeader: {
        padding: "14px 18px",
        display: "flex",
        justifyContent: "space-between",
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
        overflow: 'hidden',
        right: 0,
        bottom: 0,
    }
};

const Message = ({message}) => <div style={styles.message}>{message}</div>;
const MessageBoxHeader = ({children, icon, onToggleOpen}) => (
    <div style={styles.messageBoxHeader}>
        <span>{children}</span>
        <FontAwesomeIcon icon={['fa', icon]} onClick={onToggleOpen}/>
    </div>
);

export default function MessageDrawer({messages}) {
    const [isOpen, setOpen] = useState(false);
    const className = "drawer drawer-" + (isOpen ? "open" : "closed");
    return (
        <div style={styles.messageBox} className={className}>
            <MessageBoxHeader onToggleOpen={() => setOpen(!isOpen)} icon={isOpen ? "chevron-down" : "chevron-up"}>Messages</MessageBoxHeader>
            <div className="drawer-content">
            {
                messages.map(m => (
                    <Message key={m.uuid} message={m.body} />
                ))
            }
            </div>
        </div>
    )
}
