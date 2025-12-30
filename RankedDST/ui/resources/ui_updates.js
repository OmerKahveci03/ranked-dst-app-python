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

const matchStateElements = {
    no_match: ["no-match-footer"],
    world_generating: ["world-generating-footer"],
    world_ready: ["world-ready-footer"],
    in_progress: ["in-progress-footer"],
    completed: ["completed-footer"],
}

const matchStateDialogue = {
    no_match: {
        "top" : "Welcome back!", 
        "bot": "Ready for your next ranked match?"
    },
    world_generating: {
        "top" : "My scans indicate that a ranked match is live!", 
        "bot": "Please hold while I stablize our connection to the world..."
    },
    world_ready: {
        "top" : "I did it! Connection to the world has been established!", 
        "bot": "Please continue when ready. You have work to do!"
    },
    in_progress: {
        "top" : "I see you've made it in.", 
        "bot": "Stay focused lad! Defeat as many 'large specimen' as possible."
    },
    completed: {
        "top" : "Looks like our time is up...", 
        "bot": "We will need to wait for the other experiments to conclude."
    },
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

function replayAnimation(el, className) {
    if (!el) return;

    el.classList.remove(className);
    // Force reflow so the browser resets the animation
    void el.offsetWidth;
    el.classList.add(className);
}

function updateWagstaffDialogue(newState) {
    const dialogue = matchStateDialogue[newState];
    if (!dialogue) {
        console.warn("Unknown match state:", newState);
        return;
    }

    const topDialogue = document.getElementsByClassName("wagstaff-dialogue-top")[0];
    const botDialogue = document.getElementsByClassName("wagstaff-dialogue-bot")[0];

    topDialogue.textContent = dialogue.top;
    botDialogue.textContent = dialogue.bot;

    replayAnimation(topDialogue, "wagstaff-dialogue-top");
    replayAnimation(botDialogue, "wagstaff-dialogue-bot");
}

function matchStateChanged(newState) {
    const matchStatusElement = document.getElementById("match-status");

    matchStatusElement.textContent = newState;
    showStateElements(matchStateElements, newState);
    updateWagstaffDialogue(newState);
}


function setUserData(username) {
    const usernameElement = document.getElementById("user-name");

    usernameElement.textContent = `Logged in as ${username}`;
}

function initializeState() {
    matchStateChanged("no_match");
    connectionStateChanged("connecting-section");
}
initializeState();

// Expose this to the window
window.connectionStateChanged = connectionStateChanged;
window.setUserData = setUserData;
window.matchStateChanged = matchStateChanged;

export { connectionStateChanged, setUserData, matchStateChanged };