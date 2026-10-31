// Times and durations the way the Studio writes them: "3 h 12 m", "41 m", "11:02", "2 d 4 h".
.pragma library

function duration(seconds) {
    if (seconds === null || seconds === undefined || isNaN(seconds)) return ""
    var whole = Math.max(0, Math.round(seconds))
    var days = Math.floor(whole / 86400), hours = Math.floor(whole % 86400 / 3600)
    var minutes = Math.floor(whole % 3600 / 60)
    if (days > 0) return days + " d " + hours + " h"
    if (hours > 0) return hours + " h " + (minutes < 10 ? "0" : "") + minutes + " m"
    if (minutes > 0) return minutes + " m"
    return whole + " s"
}

function clock(time) {
    // "2026-10-31T11:02:40.120" -> "11:02"
    if (!time) return ""
    var part = String(time).split("T")
    return (part.length > 1 ? part[1] : part[0]).slice(0, 5)
}

function since(time, now) {
    // seconds from a report time to now (epoch seconds)
    if (!time) return 0
    var at = Date.parse(String(time))
    return isNaN(at) ? 0 : Math.max(0, now - at / 1000)
}

function initials(name) {
    if (!name) return "?"
    return String(name).replace(/[^A-Za-z0-9]/g, "").slice(0, 2).toLowerCase()
}

function tone(state) {
    if (state === "ok") return "ok"
    if (state === "running") return "info"
    if (state === "failed") return "danger"
    return "plain"
}

function stateText(state) {
    if (state === "ok") return "done"
    if (state === "planned") return "next"
    return state || ""
}
