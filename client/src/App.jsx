import React, {useEffect, useReducer} from "react";
import openSocket from "socket.io-client"
import AutoResizer from "react-base-table/lib/AutoResizer";
import EventTable from "./components/EventTable";
import MessageTable from "./components/MessageTable";
import TaskTable from "./components/TaskTable";
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
        ids: [],
        byId: {},
    },
    events: {
        ids: [],
        byId: {}
    },
    workers: {
        ids: [],
        byId: {}
    },
    tasks: {
        ids: [],
        byId: {}
    }
};

class Task {
    constructor({name, uuid, processed, active, args, kwargs, eta, received_at}) {
        this.name = name;
        this.uuid = uuid;
        this.processed = processed;
        this.active = active;
        this.args = args;
        this.kwargs = kwargs;
        this.eta = eta;
        this.received_at = received_at
    }
}

class Worker {
    constructor({status, hostname, processed, active, args, kwargs, eta, received_at}) {
        this.hostname = hostname;
        this.processed = processed;
        this.active = active;
        this.args = args;
        this.kwargs = kwargs;
        this.eta = eta;
        this.received_at = received_at
        this.status = status || "ONLINE"
    }
}

const dataReducer = (state = initialData, action) => {
    switch (action.type) {
        case 'LOAD_TASK': {
            const task = new Task({...action.payload});
            const tasks = {...state.tasks};
            tasks.byId[task.uuid] = task;
            tasks.ids.unshift(task.uuid);
            return {
                ...state,
                tasks,
            }
        }
        case 'UPDATE_TASK': {
            const tasks = {...state.tasks};
            console.log(action.payload);
            let task = tasks.byId[action.payload.uuid];
            tasks.byId[action.payload.uuid] = {...task, ...action.payload};
            return {
                ...state,
                tasks,
            }
        }
        case 'UPDATE_WORKER': {
            const workers = {...state.workers};
            let worker = workers.byId[action.payload.id];
            let id = action.payload.id;
            console.log(action.payload);
            if (workers.byId[id] === undefined) {
                workers.ids.push(action.payload.id)
            }
            workers.byId[action.payload.id] = {...worker, ...action.payload, status: "ONLINE"};
            return {
                ...state,
                workers: {...workers}
            }
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

const clearSessionData = () => ({
    type: 'SOCKET_CLEAR_SESSION_DATA',
});

const receiveMessage = message => ({
    type: 'SOCKET_RECEIVE_MESSAGE',
    payload: message
});

const StatusBadge = ({online}) => {
    const text = online ? "Online" : "Offline";
    const color = online ? "#1daf1d" : "red";
    return <span style={{
        backgroundColor: color,
        padding: '2px 4px',
        color: "white",
        fontSize: "11px",
        borderRadius: '2px'
    }}>{text}</span>
};

const renderStatus = status => {
    if (status === 'ONLINE') {
        return <StatusBadge online/>
    } else {
        return <StatusBadge offline/>
    }
};

const loadTask = ({payload, type}) => {
    return {
        type: "LOAD_TASK",
        payload,
        meta: {type}
    }
};

const updateTask = ({payload, type}) => {
    return {
        type: "UPDATE_TASK",
        payload,
        meta: {type}
    }
};

const updateWorker = ({payload, type}) => {
    return {
        type: "UPDATE_WORKER",
        payload,
        meta: {type}
    }
};

const addEvent = ({payload, type}) => {
    return {
        type: "ADD_EVENT",
        payload,
        meta: {
            type
        }
    }
};

const Logo = () => <div style={{padding: "8px", fontSize: "24px"}}>Fiber</div>;
const Status = ({status}) => {
    return <div style={{fontSize: "14px"}}>
        {renderStatus(status)}
    </div>
};

function Header() {
    return (
        <div className="App-header"><Logo/></div>
    )
}

const Hostname = ({children}) => <div style={{color: '#323332', fontWeight: 500, fontSize: '13px'}}>{children}</div>

const AttributeItem = ({label, value}) => (
    <div style={{alignItems: 'center', display: 'flex', flexDirection: 'row', justifyContent: 'space-between'}}>
        <Label>{label}</Label>
        <Value>{value}</Value>
    </div>
);
const Value = ({children}) => (
    <div style={{color: '#222222', fontSize: '12px'}}>
        {children}
    </div>
);

const Label = ({children}) => (
    <div style={{color: '#333333', fontSize: '12px', fontWeight: 500}}>
        {children}
    </div>
);


function WorkerCard({worker}) {
    return <div style={{
        margin: '6px',
        display: 'flex',
        minWidth: "240px",
        borderRadius: "4px",
        padding: '6px 10px',
        border: '1px solid #BBBBBB',
        flexDirection: 'column'
    }}>
        <div style={{
            marginBottom: '4px',
            alignItems: 'center',
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'space-between'
        }}>
            <Hostname>{worker.hostname}</Hostname>
            <Status status={worker.status}/>
        </div>
        <AttributeItem value={worker.processed} label="Processed"/>
        <AttributeItem value={worker.active} label="Active"/>
        <AttributeItem value={worker.clock} label="Uptime"/>
    </div>
}

function WorkersOverview({workers = []}) {
    return (
        <div style={{display: 'flex', padding: "0 12px", maxWidth: '100vw', overflowX: 'scroll'}}>
            {workers.map(worker => <WorkerCard key={worker.id} worker={worker}/>)}
        </div>
    )
}

function App() {
    const [data, dataDispatch] = useReducer(dataReducer, initialData);
    const [session, sessionDispatch] = useReducer(sessionReducer, initialSession);
    const {tasks, workers, events, messages} = data;

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

        socket.on('event', event => {
            switch (event.action) {
                case "LOAD_TASK":
                    dataDispatch(loadTask(event));
                    break;
                case "UPDATE_TASK":
                    dataDispatch(updateTask(event));
                    break;
                case "UPDATE_WORKER":
                    dataDispatch(updateWorker(event));

                    break;
                default:
                    console.error(`${event.action} is not a valid action type.`)
            }
        });
    }, []);

    return (
        <div className="App">
            <Header/>
            <WorkersOverview workers={ordered(workers)}/>
            <Container style={{width: "100%"}}>
                <AutoResizer height={400}>
                    {({width, height}) => {
                        console.log(width, height);
                        return <TaskTable width={width} height={height} tasks={ordered(tasks)} />
                    }}
                </AutoResizer>
                <EventTable events={ordered(events)}/>
            </Container>
            <MessageTable messages={ordered(messages)}/>
        </div>
    );
}

function ordered({byId, ids}) {
    return ids.map(id => byId[id])
}

export default App;
