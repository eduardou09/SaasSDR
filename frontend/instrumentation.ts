/**
 * Next.js instrumentation hook — roda no worker Node.js antes de qualquer SSR.
 *
 * Problema: Node.js v22+ define `localStorage` como built-in WinterCG, mas
 * depende de `--localstorage-file` para inicializar o storage. O Next.js 15.3.x
 * passa esse flag com um path inválido/vazio, então `localStorage.getItem` lança
 * TypeError mesmo com o objeto definido. O Clerk usa localStorage em dev mode
 * para o dev-browser token, quebrando todas as rotas com 500.
 *
 * Fix: substitui o localStorage quebrado por uma implementação em memória, ativa
 * somente no runtime Node.js (SSR). Auth via cookies não é afetada.
 */
export function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const store = new Map<string, string>();
    const impl = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
      clear: () => {
        store.clear();
      },
      key: (index: number) => [...store.keys()][index] ?? null,
      get length() {
        return store.size;
      },
    };

    // Node.js v22+ define localStorage como built-in mas pode estar quebrado
    // quando --localstorage-file não tem path válido. Sobrescrevemos sempre.
    try {
      Object.defineProperty(globalThis, "localStorage", {
        value: impl,
        writable: true,
        configurable: true,
      });
    } catch {
      // Fallback caso defineProperty falhe (e.g. non-configurable)
      (globalThis as unknown as Record<string, unknown>)["localStorage"] = impl;
    }
  }
}
