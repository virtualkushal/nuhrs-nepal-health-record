import { createContext, useContext, useState, useCallback } from "react";

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null);

  const show = useCallback((message, kind = "") => {
    setToast({ message, kind });
    setTimeout(() => setToast(null), 3200);
  }, []);

  const styles = {
    ok: "bg-ok text-white",
    err: "bg-error text-white",
    "": "bg-inverse-surface text-white bg-[#2e3132]",
  };

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-[100] px-5 py-3 rounded-xl shadow-2xl font-label-md ${
            styles[toast.kind] || styles[""]
          }`}
        >
          {toast.message}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
