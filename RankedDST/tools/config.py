import os, json
import webview

from RankedDST.tools import state

CONFIG_KEYS = ["klei_secret_dev", "klei_secret", "dedicated_server_path"]

def get_config_path() -> str:
    """
    Returns the path to the config.json file containing saved configuration/auth data. Creates the path
    if not already present.

    Returns
    -------
    config_fp: str
        The full file path to the configuration json file.
    """

    home = os.path.expanduser("~")
    base_path = os.path.join(home, ".ranked_dst")
    config_fp = os.path.join(base_path, "config.json")

    os.makedirs(base_path, exist_ok=True)

    return config_fp

def save_data(save_values: dict[str, str]) -> None:
    """
    Writes the values provided to the configuration file.

    Parameters
    ----------
    save_values: dict[str, str]
        The values to be written to the json file
    """
    if any(save_key not in CONFIG_KEYS for save_key in save_values.keys()):
        raise ValueError(
            f"Tried to save an invalid key to the json file\n"
            f"\tProvided: {save_values}\n"
            f"\tMust be in: {CONFIG_KEYS}\n"
        )

    config_fp = get_config_path()
    if os.path.exists(config_fp):
        with open(config_fp, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}

    config.update(save_values)

    with open(config_fp, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def load_initial_state(window: webview.Window) -> None:
    """
    Loads the ~/home/.ranked_dst/config.json file and reads the data found.
    """

    print("Loading initial state...")
    config_fp = get_config_path()
    with open(config_fp, "r", encoding="utf-8") as file:
        config_data: dict[str, str] = json.load(file)
        print(f"Read {config_data} into config data!")

    secret_key = "klei_secret_dev" if state.DEVELOPING else "klei_secret"

    klei_secret = config_data.get(secret_key, None)
    if klei_secret:
        print(f"Klei secret was stored as {klei_secret}")
        state.set_user_data({"klei_secret" : klei_secret})
    else:
        print("No klei secret was stored.")

    print(f"User data state is now: {state.get_user_data()}")

    state.set_match_state(state.MatchNone, window=window)
    state.set_connection_state(state.ConnectionNotConnected, window=window)  # might want to remove this actually
