import React, { useEffect, useMemo, useReducer } from "react";
import openSocket from "socket.io-client"
import EventTable from "./components/EventTable";
import MessageTable from "./components/MessageTable";
import Container from "./components/Container"

import './App.css';

const initialSession = {
    socket: {
        room: null,
        sid: null,
    }
};

const initialData = {
    messages: {
        all: [],
        byId: new Map([])
    },
    events: {
        all: [],
        byId: new Map([]),
        lastHeartbeat: null,
    },
    tasks: {
        all: [],
        byId: new Map([])
    },
    meta: {
        lastHeartbeat: null,
    }
};

const dataReducer = (state = initialData, action) => {
    switch (action.type) {
        case 'SOCKET_RECEIVE_WORKER_EVENT': {
            return {
                ...state,
                meta: {
                    ...state.meta,
                    lastHeartbeat: new Date(action.payload.timestamp * 1000),
                }
            }
        }
        case 'SOCKET_RECEIVE_TASK_EVENT': {
            const all = [action.payload, ...state.events.all];
            const byId = new Map(all.map(e => [e.uuid, e]));
            return { ...state, events: { ...state.events, byId, all } };
        }
        case 'SOCKET_RECEIVE_MESSAGE': {
            const all = [action.payload, ...state.messages.all];
            const pairs = all.map(m => [m, m]);
            const byId = new Map(pairs);
            return { ...state, messages: { ...state.messages, byId, all } }
        }
        default:
            return state
    }
};


function sessionReducer(state = initialSession, action) {
    switch (action.type) {
        case 'SOCKET_RECEIVE_SID': {
            const sid = action.payload;
            const socket = { ...state.socket, sid };
            return { ...state, socket }
        }
        case 'SOCKET_CLEAR_SESSION_DATA': {
            const socket = { ...initialSession.socket };
            return { ...state, socket };
        }
        default:
            return state;
    }
}

const receiveSid = sid => ({
    type: 'SOCKET_RECEIVE_SID',
    payload: sid
});

const receiveWorkerEvent = data => ({
    type: 'SOCKET_RECEIVE_WORKER_EVENT',
    payload: data,
});

const receiveTaskEvent = data => ({
    type: 'SOCKET_RECEIVE_TASK_EVENT',
    payload: data,
});

const clearSessionData = () => ({
    type: 'SOCKET_CLEAR_SESSION_DATA',
});

const receiveMessage = message => ({
    type: 'SOCKET_RECEIVE_MESSAGE',
    payload: message
});

const StatusBadge = ({offline, online}) => {
    const text = online ? "Online" : "Offline";
    const color = online ? "#1daf1d" : "red";
    return <span style={{backgroundColor: color, padding: '2px 4px', color: "white", fontSize: "11px", borderRadius: '2px'}}>{text}</span>
}

const renderStatus = status => {
    if (status === 'ONLINE') {
        return <StatusBadge online />
    } else {
        return <StatusBadge offline />
    }
}

const Logo = () => <div style={{ padding: "8px", fontSize: "24px" }}>Fiber</div>;
const Status = ({ status }) => {
    return <div style={{ fontSize: "14px" }}>
        {renderStatus(status)}
    </div>
};

function Header() {
    return (
        <div className="App-header"><Logo /></div>
    )
}

const WORKERS = [
    {
        hostname: 'celery@worker-1',
        status_string: 'ONLINE',
        processed: 921,
        failed: 0,
        uptime: 1029120.0,
        active: 1,
        current_task: 'example.calculate_it_all'
    },
    {
        hostname: 'celery@worker-2',
        status_string: 'ONLINE',
        failed: 0,
        processed: 829,
        uptime: 102999.0,
        active: 0,
        current_task: 'N/A'
    },
    {
        hostname: 'celery@worker-3',
        status_string: 'OFFLINE',
        failed: 22,
        processed: 0,
        uptime: 0.0,
        active: 0,
        current_task: 'N/A'
    }
]
const Hostname = ({ children }) => <div style={{ color: '#323332', fontWeight: 500, fontSize: '13px' }}>{children}</div>

const AttributeItem = ({label, value}) => (
   <div style={{ alignItems: 'center', display: 'flex', flexDirection: 'row', justifyContent: 'space-between' }}>
       <Label>{label}</Label>
       <Value>{value}</Value>
   </div>
)
const Value = ({children}) => (
    <div style={{color: '#222222', fontSize: '12px'}}>
        {children}
    </div>
)

const Label = ({children}) => (
    <div style={{color: '#333333', fontSize: '12px', fontWeight: 500}}>
        {children}
    </div>
)


function WorkerCard({ worker }) {
    return <div style={{ margin: '6px', display: 'flex', minWidth: "240px", borderRadius: "4px", padding: '6px 10px', border: '1px solid #BBBBBB', flexDirection: 'column'}}>
        <div style={{ marginBottom: '4px', alignItems: 'center', display: 'flex', flexDirection: 'row', justifyContent: 'space-between' }}>
            <Hostname>{worker.hostname}</Hostname>
            <Status status={worker.status_string} />
        </div>
        <AttributeItem value={worker.processed} label="Processed" />
        <AttributeItem value={worker.failed} label="Failed" />
        <AttributeItem value={worker.active} label="Active" />
        <AttributeItem value={worker.uptime} label="Uptime" />
    </div>
}
function WorkersOverview({ workers = [] }) {
    return (
        <div style={{display: 'flex', maxWidth: '600px'}}>
            {workers.map(worker => <WorkerCard key={worker.id} worker={worker} />)}
        </div>
    )
}

function App() {
    const [data, dataDispatch] = useReducer(dataReducer, initialData);
    const [session, sessionDispatch] = useReducer(sessionReducer, initialSession);
    const { tasks, meta, events, messages } = data;

    useEffect(() => {
        const socket = openSocket('http://localhost:8080');
        socket.on('connect', data => {
            sessionDispatch(receiveSid(data))
        });

        socket.on('disconnect', () => {
            sessionDispatch(clearSessionData());
        });

        socket.on('message', data => {
            dataDispatch(receiveMessage(data));
        });

        socket.on('event', data => {
            if (data.type.startsWith("task-")) {
                dataDispatch(receiveTaskEvent(data))
            } else if (data.type.startsWith("worker-")) {
                dataDispatch(receiveWorkerEvent(data))
            }
        });
    }, []);

    return (
        <div className="App">
            <Header />
            <WorkersOverview workers={WORKERS} />
            <Container>
                <EventTable events={events.all} />
            </Container>
            <MessageTable messages={messages.all} />
        </div>
    );
}

export default App;
