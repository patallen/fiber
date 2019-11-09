export const bringWorkerOnline = payload => ({
    type: 'BRING_WORKER_ONLINE',
    payload
});

export const takeWorkerOffline = payload => ({
    type: 'TAKE_WORKER_OFFLINE',
    payload
});

export const receiveSid = sid => ({
    type: 'SOCKET_RECEIVE_SID',
    payload: sid
});

export const clearSessionData = () => ({
    type: 'SOCKET_CLEAR_SESSION_DATA',
});

export const receiveMessage = message => ({
    type: 'SOCKET_RECEIVE_MESSAGE',
    payload: message
});

export const loadTask = ({payload, type}) => {
    return {
        type: "LOAD_TASK",
        payload,
        meta: {type}
    }
};

export const updateTask = ({payload, type}) => {
    return {
        type: "UPDATE_TASK",
        payload,
        meta: {type}
    }
};

export const updateWorker = ({payload, type}) => {
    return {
        type: "UPDATE_WORKER",
        payload,
        meta: {type}
    }
};

export const completeTask = ({payload, type}) => {
    return {
        type: "COMPLETE_TASK",
        payload,
        meta: {type}
    }
};

export const addEvent = ({payload, type}) => {
    return {
        type: "ADD_EVENT",
        payload,
        meta: {
            type
        }
    }
};

