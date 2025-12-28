/*
    This script contains functions only meant to call the python part of the program

    They are called from actions such as button clicks or form fillouts
*/


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