import React, {useEffect, useMemo, useReducer} from "react";
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
            return {...state, events: {...state.events, byId, all}};
        }
        case 'SOCKET_RECEIVE_MESSAGE': {
            const all = [action.payload, ...state.messages.all];
            const pairs = all.map(m => [m, m]);
            const byId = new Map(pairs);
            return {...state, messages: {...state.messages, byId, all}}
        }
        default:
            return state
    }
};


function sessionReducer(state = initialSession, action) {
    switch (action.type) {
        case 'SOCKET_RECEIVE_SID': {
            const sid = action.payload;
            const socket = {...state.socket, sid};
            return {...state, socket}
        }
        case 'SOCKET_CLEAR_SESSION_DATA': {
            const socket = {...initialSession.socket};
            return {...state, socket};
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

const Logo = () => <div style={{padding: "8px", fontSize: "24px"}}>Fiber</div>;
const Status = ({lastHeartbeat}) => {
    return <div style={{padding: "8px", fontSize: "24px"}}>
        {lastHeartbeat ? lastHeartbeat.toISOString() : "N/A"}
    </div>
};

function Header({lastHeartbeat}) {
    return (
        <div className="App-header">
            <Logo />
            <Status lastHeartbeat={lastHeartbeat} />
        </div>
    )
}


function App() {
    const [data, dataDispatch] = useReducer(dataReducer, initialData);
    const [session, sessionDispatch] = useReducer(sessionReducer, initialSession);
    const {tasks, meta, events, messages} = data;
    const hasSession = useMemo(() => !!session.socket.uuid, [session]);

    useEffect(() => {
        const socket = openSocket('http://fib.re:8080');
        socket.on('connect', data => {
            sessionDispatch(receiveSid(data))
        });

        socket.on('disconnect', () => {
            sessionDispatch(clearSessionData());
        });

        socket.on('message', data => {
            dataDispatch(receiveMessage(data));
        });

        socket.on('task-update', data => {
            console.log('task-update received', data);
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
            <Header lastHeartbeat={meta.lastHeartbeat} />
            <Container>
                <EventTable events={events.all}/>
            </Container>
            <MessageTable messages={messages.all}/>
        </div>
    );
}

export default App;
