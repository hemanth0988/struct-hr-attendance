// today.js — shared across all pages

const TODAY_KEY = "manual_today_struct_hr";

// Save
function setManualToday(val) {
    localStorage.setItem(TODAY_KEY, val);
}

// Read
function getManualToday() {
    return localStorage.getItem(TODAY_KEY);
}

// Auto-inject small Today bar if placeholder exists
document.addEventListener("DOMContentLoaded", () => {
    const bar = document.getElementById("today-bar");
    if (!bar) return;

    const value = getManualToday() || "";

    bar.innerHTML = `
        <div style="padding: 10px; background: #eee; margin-bottom: 10px;">
            <label><b>Today:</b></label>
            <input type="date" id="today-input" value="${value}">
        </div>
    `;

    document.getElementById("today-input").addEventListener("change", (e) => {
        setManualToday(e.target.value);
        document.dispatchEvent(new CustomEvent("todayChanged"));
    });
});
