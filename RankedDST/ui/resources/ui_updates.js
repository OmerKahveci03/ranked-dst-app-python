/*
    This script contains functions called by the python-end only.

    They are meant to mutate the user interface.
*/

// The list of elements to display for the given connection state
const connectionStateElements = {
    not_connected: ["not-connected-section", "not-connected-main"],
    no_server: ["no-connection-section", "no-server-main"],
    connecting: ["connecting-section", "connecting-main"],
    connected: ["connected-section", "connected-main"],
}

// Hides all elements for the state map (excluding the ones for the newState)
function showStateElements(stateElementMap, newState) {
    const allIds = new Set(
        Object.values(stateElementMap).flat()
    );

    for (const id of allIds) {
        const el = document.getElementById(id);
        if (el) el.style.display = "none";
    }
    const idsToShow = stateElementMap[newState] || [];

    for (const id of idsToShow) {
        const el = document.getElementById(id);
        if (el) el.style.display = "";
    }
}

// Updates the UI based on the new connection state
function connectionStateChanged(newState) {
    console.log("Connection state: ", newState);

    showStateElements(connectionStateElements, newState);
}

function matchStateChanged(newState) {
    const matchStatusElement = document.getElementById("match-status")

    matchStatusElement.textContent = newState
}


function setUserData(username) {
    const usernameElement = document.getElementById("user-name");

    usernameElement.textContent = `Logged in as ${username}`;
}

// Expose this to the window
window.connectionStateChanged = connectionStateChanged;
window.setUserData = setUserData;
window.matchStateChanged = matchStateChanged;

export { connectionStateChanged, setUserData, matchStateChanged }