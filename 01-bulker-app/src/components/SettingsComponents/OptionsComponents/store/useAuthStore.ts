import {create} from "zustand";

type AuthStore = {
    /**
     * The authentication status of the application.
     */
    auth: boolean,
    /**
     * Used to track the progress of the asynchronous authentication
     * call.
     */
    isAuthenticating: boolean,
    /**
     * Sets the authenication status to the given status.
     * @param status The boolean status
     * @returns 
     */
    setAuthStatus: (status: boolean) => void,
    /**
     * Sets the authenticating status progress before, during, and after the call.
     * @param status The boolean status
     * @returns 
     */
    setIsAuthenticating: (status: boolean) => void,
}

export const useAuthStore = create<AuthStore>((set) => ({
    auth: false,
    isAuthenticating: false,
    setAuthStatus: (status) => set(prev => ({...prev, auth: status})),
    setIsAuthenticating: (status) => set(prev => ({...prev, isAuthenticating: status})),
}));