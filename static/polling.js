function applyProfile() {
    const profiles =
        window.NOWFRAME_POLLING_PROFILES || {};

    const selector = document.getElementById(
        "polling_profile"
    );

    if (!selector) {
        return;
    }

    const profile = selector.value;
    const custom = profile === "custom";

    for (const field of [
        "playing",
        "paused",
        "idle",
        "unapproved"
    ]) {
        const input = document.getElementById(field);

        if (!input) {
            continue;
        }

        input.disabled = !custom;

        if (!custom && profiles[profile]) {
            input.value = profiles[profile][field];
        }
    }
}

window.addEventListener(
    "DOMContentLoaded",
    applyProfile
);
