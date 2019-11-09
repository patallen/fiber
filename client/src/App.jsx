import React, {useEffect, useReducer} from "react";
import openSocket from "socket.io-client"
import AutoResizer from "react-base-table/lib/AutoResizer";
import MessageDrawer from "./components/MessageDrawer";
import TaskTable from "./components/TaskTable";
import Container from "./components/Container"
import {StatusBadge} from "./components/Badge";
import * as actions from "./actions";
import './App.css';

import { library } from '@fortawesome/fontawesome-svg-core'
import {faChevronDown, faChevronUp} from "@fortawesome/free-solid-svg-icons"

library.add(faChevronDown, faChevronUp);

const renderStatus = status => {
    if (status === 'ONLINE') {
        return <StatusBadge online/>
    } else {
        return <StatusBadge offline/>
    }
};

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


const dataReducer = (state = initialData, action) => {
    switch (action.type) {
        case 'LOAD_TASK': {
            const tasks = {...state.tasks};
            tasks.byId[action.payload.uuid] = action.payload;
            tasks.ids.unshift(action.payload.uuid);
            return { ...state,  tasks }
        }
        case 'UPDATE_TASK': {
            const tasks = {...state.tasks};
            const task = {...tasks.byId[action.payload.uuid]};
            tasks.byId[action.payload.uuid] = {...task, ...action.payload};
            return {
                ...state,
                tasks: {
                    ...state.tasks,
                    [action.payload.uuid]: {...task}
                }
            }
        }
        case "COMPLETE_TASK": {
            const tasks = {...state.tasks};
            tasks.byId[action.payload.uuid] = {...tasks.byId[action.payload.uuid], ...action.payload};
            return {...state,  tasks}
        }
        case "TAKE_WORKER_OFFLINE": {
            const workers = {...state.workers};
            Object.assign(workers.byId[action.payload.id], action.payload);
            return {...state, workers};
        }
        case "BRING_WORKER_ONLINE": {
            const workers = {...state.workers};
            workers.byId[action.payload.id] = action.payload;
            return {...state, workers};
        }
        case 'UPDATE_WORKER': {
            const workers = {...state.workers};
            let worker = workers.byId[action.payload.id];
            let id = action.payload.id;
            if (workers.byId[id] === undefined) {
                workers.ids.push(action.payload.id)
            }
            workers.byId[action.payload.id] = {...worker, ...action.payload};
            return {...state,  workers}
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
            sessionDispatch(actions.receiveSid(data))
        });

        socket.on('disconnect', () => {
            sessionDispatch(actions.clearSessionData());
        });

        socket.on('message', data => {
            dataDispatch(actions.receiveMessage(data));
        });

        socket.on('event', event => {
            switch (event.action) {
                case "LOAD_TASK":
                    dataDispatch(actions.loadTask(event));
                    break;
                case "UPDATE_TASK":
                    dataDispatch(actions.updateTask(event));
                    break;
                case "UPDATE_WORKER":
                    dataDispatch(actions.updateWorker(event));
                    break;
                case "TAKE_WORKER_OFFLINE":
                    dataDispatch(actions.takeWorkerOffline(event));
                    break;
                case "BRING_WORKER_ONLINE":
                    dataDispatch(actions.bringWorkerOnline(event));
                    break;
                case "COMPLETE_TASK":
                    dataDispatch(actions.completeTask(event));
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
                <AutoResizer height={500}>
                    {({width, height}) => {
                        return <TaskTable width={width} height={height} tasks={ordered(tasks)} />
                    }}
                </AutoResizer>
            </Container>
            <MessageDrawer messages={ordered(messages)}/>
        </div>
    );
}

function ordered({byId, ids}) {
    return ids.map(id => byId[id])
}

export default App;
