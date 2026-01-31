export type ErrorEvent = {
    title?: string;
    message: string;
    code?: string;
    details?: any;
};

type Listener = (e: ErrorEvent) => void;

class ErrorBus {
    private listeners: Listener[] = [];

    emit(error: ErrorEvent) {
        this.listeners.forEach(l => l(error));
    }

    subscribe(listener: Listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }
}

export const errorBus = new ErrorBus();
