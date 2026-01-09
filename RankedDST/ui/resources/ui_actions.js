/*
    This script contains functions only meant to call the python part of the program

    They are called from actions such as button clicks or form fillouts
*/
import { connectionStateChanged, setUserData, matchStateChanged } from "./ui_updates.js";

function saveProxySecret() {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }

    const secretInput = document.getElementById("proxy-secret-input");
    const secretValue = secretInput.value.trim();

    if (!secretValue) return
    
    
    window.pywebview.api.save_proxy_secret(secretValue);

    // pause the ui or something
}

function onStopServerClicked() {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }
    
    window.pywebview.api.stop_server_button();
}

function onLogoutClicked() {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return;
    }
    
    // This is state.ConnectionNotConnected
    connectionStateChanged("not_connected");

    // This is state.MatchNone
    matchStateChanged("no_match");

    setUserData("");

    window.pywebview.api.logout_button();
}

function onOpenWebsite(page) {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }
    
    window.pywebview.api.open_website(page);
}

function onOpenFileExplorer(searchType){
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }

    const searchTypes = ['dedi_path', 'cluster_path'];
    if (!searchTypes.includes(searchType)) {
        return
    }
    const dediPath = searchType === 'dedi_path';
    
    window.pywebview.api.open_file_explorer_ui(dediPath);
}

const dediPathInput = document.getElementById("dedi-path-input");
const clusterPathInput = document.getElementById("cluster-path-input");

dediPathInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        onSubmitPath(dediPathInput.value, 'dedi_path');
    }
});

clusterPathInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        onSubmitPath(clusterPathInput.value, 'cluster_path');
    }
});

function onSubmitPath(path, searchType){
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }
    const searchTypes = ['dedi_path', 'cluster_path'];
    if (!searchTypes.includes(searchType)) {
        return
    }
    const dediPath = searchType === 'dedi_path';
    
    window.pywebview.api.submit_path(path, dediPath);
}
// Expose this to the window
window.saveProxySecret = saveProxySecret;
window.onStopServerClicked = onStopServerClicked;
window.onLogoutClicked = onLogoutClicked;
window.onOpenWebsite = onOpenWebsite;
window.onOpenFileExplorer = onOpenFileExplorer;
window.onSubmitPath = onSubmitPath;
