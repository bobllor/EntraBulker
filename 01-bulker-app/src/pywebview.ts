export {};

// imported into files where pywebview calls to prevent IDE errors.
declare global{
    interface Window{
        pywebview: any;
    }
}