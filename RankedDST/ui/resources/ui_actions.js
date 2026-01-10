/*
    This script contains functions only meant to call the python part of the program

    They are called from actions such as button clicks or form fillouts
*/

import { connectionStateChanged, setUserData, matchStateChanged } from "./ui_updates.js";

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

var loginButtonLocked = false;
async function lockLoginButton(lockDurationSeconds) {
    if (loginButtonLocked) {
        return
    };

    const btn = document.getElementById("login-button");
    if (btn) {
        btn.style.opacity = "0.5";
        btn.style.pointerEvents = "none";
    }

    loginButtonLocked = true;

    await sleep(lockDurationSeconds * 1000);
    
    if (btn) {
        btn.style.opacity = "";
        btn.style.pointerEvents = "";
    }
    loginButtonLocked = false;
}

function handleLoginClicked() {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }

    if (loginButtonLocked) {
        return
    }
    

    const usernameInput = document.getElementById("login-username-input");
    const usernameValue = usernameInput.value.trim();

    if (!usernameValue) return;

    const passwordInput = document.getElementById("login-password-input");
    const passwordValue = passwordInput.value.trim();

    if (!passwordValue) return;
    
    lockLoginButton(5);
    window.pywebview.api.login_clicked(usernameValue, passwordValue);
}

function onLogoutClicked() {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return;
    }

    window.pywebview.api.logout_button();
}

function onStopServerClicked() {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }
    
    window.pywebview.api.stop_server_button();
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
window.handleLoginClicked = handleLoginClicked;
window.onStopServerClicked = onStopServerClicked;
window.onLogoutClicked = onLogoutClicked;
window.onOpenWebsite = onOpenWebsite;
window.onOpenFileExplorer = onOpenFileExplorer;
window.onSubmitPath = onSubmitPath;
