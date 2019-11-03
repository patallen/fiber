class FiberEvent { }

class TaskEvent extends FiberEvent {
    constructor({
        type,
        hostname,
        state,
        uuid,
        clock,
        utcoffset,
        result,
        timestamp,
        pid,
        localReceived
    }) {
        super();
        this.pid = parseInt(pid)
        this.uuid = uuid
        this.type = type;
        this.hostname = hostname;
        this.state = state;
        this.clock = clock;
        this.utcoffset = utcoffset;
        this.result = result;
        this.timestamp = new Date(timestamp)
        this.localReceived = new Date(localReceived)
    }

    static loadObject = ({local_received: localReceived, ...rest}) => {
        return new TaskEvent({...rest, localReceived})
    }
}
