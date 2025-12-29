/*
    This script contains functions only meant to call the python part of the program

    They are called from actions such as button clicks or form fillouts
*/
import { connectionStateChanged, setUserData, matchStateChanged } from "./ui_updates.js";

function onPress() {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }
    
    window.pywebview.api.test_button();
}

function saveKleiSecret() {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }

    const secretInput = document.getElementById("klei-secret-input");
    const secretValue = secretInput.value.trim();

    if (!secretValue) return
    
    
    window.pywebview.api.save_klei_secret(secretValue);

    // pause the ui or something
}

function onStartServerClicked() {
    if (!window.pywebview) {
        console.error("pywebview not ready");
        return
    }
    
    window.pywebview.api.start_server_button();
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

// Expose this to the window
window.onPress = onPress;
window.saveKleiSecret = saveKleiSecret;
window.onStartServerClicked = onStartServerClicked;
window.onStopServerClicked = onStopServerClicked;
window.onLogoutClicked = onLogoutClicked;
window.onOpenWebsite = onOpenWebsite;