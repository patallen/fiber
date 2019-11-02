class EventList {
    constructor(events=[]) {
        this._events = events;
        this._dirty = false;
    }

    push(event) {
        this.dirty = true;
        return this.events.unshift(event);
    }

    set dirty(value) {
        console.log(`setting dirty: ${value}`)
        this._dirty = value;
        return this._dirty;
    }

    get dirty() {
        return this._dirty
    }

    get length() {
        return this.events.length
    }
    
    get events() {
        this.dirty = false;
        return [...this._events];
    }
}
