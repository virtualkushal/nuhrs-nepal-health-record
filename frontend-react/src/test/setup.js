// Test bootstrap.
//
// Recent Node versions expose an experimental global `localStorage` that
// shadows jsdom's implementation but does not provide the Web Storage methods,
// so `window.localStorage.getItem` blows up on import of lib/api.js. Install a
// small in-memory Storage when the ambient one is unusable.
class MemoryStorage {
  #data = new Map();

  get length() {
    return this.#data.size;
  }

  key(index) {
    return [...this.#data.keys()][index] ?? null;
  }

  getItem(key) {
    return this.#data.has(String(key)) ? this.#data.get(String(key)) : null;
  }

  setItem(key, value) {
    this.#data.set(String(key), String(value));
  }

  removeItem(key) {
    this.#data.delete(String(key));
  }

  clear() {
    this.#data.clear();
  }
}

function install(name) {
  const existing = globalThis[name];
  if (existing && typeof existing.getItem === "function") return;
  Object.defineProperty(globalThis, name, {
    value: new MemoryStorage(),
    writable: true,
    configurable: true,
  });
}

install("localStorage");
install("sessionStorage");
