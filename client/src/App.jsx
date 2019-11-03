import React, {useEffect, useMemo, useReducer} from "react";
import openSocket from "socket.io-client"
import './App.css';
import EventTable from "./components/EventTable";
import MessageTable from "./components/EventTable";

const initialEvents = {
    events: [],
    byId: new Map([])
};

function eventsReducer(state = initialEvents, action) {
    switch (action.type) {
        case 'SOCKET_RECEIVE_TASK_EVENT':
        case 'SOCKET_RECEIVE_WORKER_EVENT': {
            const messages = [action.payload, ...state.events];
            const byId = new Map(messages.map(m => [m.uuid, m]));
            return {byId, messages};
        }
        default:
            return state
    }
}

const initialMessages = {
    messages: [],
    byId: new Map([])
};

function messageReducer(state = initialMessages, action) {
    switch (action.type) {
        case 'SOCKET_RECEIVE_MESSAGE': {
            const messages = [action.payload, ...state.messages];
            const pairs = messages.map(m => [m.uuid, m]);
            const byId = new Map(pairs);
            return {byId, messages}
        }
        default:
            return state
    }
}

const initialSession = {
    socket: {
        room: null,
        sid: null,
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


function App() {
    const [session, sessionDispatch] = useReducer(sessionReducer, initialSession);
    const [events, eventDispatch] = useReducer(eventsReducer, initialEvents);
    const [messages, messageDispatch] = useReducer(messageReducer, initialMessages);
    const hasSession = useMemo(() => !!session.socket.uuid, [session]);

    useEffect(() => {
        const socket = openSocket('http://fib.re:8080');
        socket.on('connect', data => {
            console.log(`connected: data=${JSON.stringify(data, null, 2)}`);
            sessionDispatch(receiveSid(data))
        });

        socket.on('disconnect', data => {
            console.log(`disconnected: data=${JSON.stringify(data, null, 2)}`);
            sessionDispatch(clearSessionData())
        });

        socket.on('message', data => {
            console.log(`Message: data=${JSON.stringify(data, null, 2)}`);
            if (data.type.startsWith("task-")) {
                messageDispatch(receiveMessage(data))
            }
        });

        socket.on('event', data => {
            console.log(`Event: data=${JSON.stringify(data, null, 2)}`);
            if (data.type.startsWith("task-")) {
                eventDispatch(receiveTaskEvent(data))
            }
        });
    });

    const backgroundColor = hasSession ? "green" : "red";

    return (
        <div className="App" style={{backgroundColor}}>
            <EventTable data={events}/>
            <MessageTable data={messages} />
        </div>
    );
}

export default App;
