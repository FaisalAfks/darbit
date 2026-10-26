// The connection to darbit's local server: requests, events and binary frames.
// See docs/tasks/T05-local-server.md; message types are in packages/darbit/src/darbit/server/protocol.py.

type Listener = (data: any) => void;

export interface Frame {
  header: { type: string; id?: number; w: number; h: number; format: string };
  bytes: ArrayBuffer;
}

let socket: WebSocket | null = null;
let nextId = 1;
const waiting = new Map<number, { resolve: (v: any) => void; reject: (e: Error) => void }>();
const listeners = new Map<string, Set<Listener>>();
const frameListeners = new Set<(frame: Frame) => void>();

/** Connect with the port and token the window was opened with (?port=…&token=…). */
export function connect(): Promise<void> {
  const params = new URLSearchParams(location.search);
  const port = params.get("port");
  if (!port) {
    // opened on its own (npm run dev, a plain file server): no server to talk to
    return Promise.reject(new Error("opened without darbit's server"));
  }
  const url = `ws://127.0.0.1:${port}/ws?token=${params.get("token")}`;
  socket = new WebSocket(url);
  socket.binaryType = "arraybuffer";
  socket.onmessage = (event) => (typeof event.data === "string" ? onText(event.data) : onBinary(event.data));
  // TODO(T05): reconnect with backoff; show a toast while disconnected
  return new Promise((resolve, reject) => {
    socket!.onopen = () => resolve();
    socket!.onerror = () => reject(new Error("darbit's server isn't running"));
  });
}

export function request<T = any>(type: string, data: object = {}): Promise<T> {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return Promise.reject(new Error("not connected to darbit's server"));
  }
  const id = nextId++;
  socket.send(JSON.stringify({ type, id, data }));
  return new Promise((resolve, reject) => waiting.set(id, { resolve, reject }));
}

export function on(type: string, listener: Listener): () => void {
  if (!listeners.has(type)) listeners.set(type, new Set());
  listeners.get(type)!.add(listener);
  return () => listeners.get(type)!.delete(listener);
}

export function onFrame(listener: (frame: Frame) => void): () => void {
  frameListeners.add(listener);
  return () => frameListeners.delete(listener);
}

function onText(text: string): void {
  const message = JSON.parse(text);
  if (message.type === "reply") {
    const pending = waiting.get(message.id);
    waiting.delete(message.id);
    if (message.error) pending?.reject(new Error(message.error));
    else pending?.resolve(message.data);
    return;
  }
  listeners.get(message.type)?.forEach((listener) => listener(message.data));
}

function onBinary(buffer: ArrayBuffer): void {
  const length = new DataView(buffer).getUint32(0);
  const header = JSON.parse(new TextDecoder().decode(new Uint8Array(buffer, 4, length)));
  const frame = { header, bytes: buffer.slice(4 + length) };
  frameListeners.forEach((listener) => listener(frame));
}
