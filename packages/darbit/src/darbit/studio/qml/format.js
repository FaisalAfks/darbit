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

function clockOf(seconds) {
    // seconds since midnight -> "11:02"
    if (seconds === null || seconds === undefined || isNaN(seconds)) return ""
    var whole = Math.max(0, Math.round(seconds)) % 86400
    var hours = Math.floor(whole / 3600), minutes = Math.floor(whole % 3600 / 60)
    return (hours < 10 ? "0" : "") + hours + ":" + (minutes < 10 ? "0" : "") + minutes
}

function dayName(day) {
    // "2026-10-31" -> "Today", "Yesterday" or "Sat 31 Oct"
    if (!day) return ""
    var parts = String(day).split("-")
    var date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
    var today = new Date(); today.setHours(0, 0, 0, 0)
    var days = Math.round((today - date) / 86400000)
    if (days === 0) return "Today"
    if (days === 1) return "Yesterday"
    return Qt.formatDate(date, "ddd d MMM")
}

function timer(seconds) {
    // 42.5 -> "0:42", 3725 -> "1:02:05"
    var whole = Math.max(0, Math.floor(seconds || 0))
    var hours = Math.floor(whole / 3600), minutes = Math.floor(whole % 3600 / 60), rest = whole % 60
    var tail = (rest < 10 ? "0" : "") + rest
    if (hours > 0) return hours + ":" + (minutes < 10 ? "0" : "") + minutes + ":" + tail
    return minutes + ":" + tail
}

function stepIcon(step) {
    var kinds = { key: "⌨", write: "✎", wait: "◷", mouse: "●", tape: "▶", check: "▣", "if": "?", loop: "↻", call: "↗", code: "{}" }
    return kinds[step.kind] || "·"
}

function stepText(step) {
    // a step as one plain line: "Press E", "Wait 0.5 s", "Click Lobby.Play", "Play the tape from 0 to 42.5 s"
    var args = step.args || {}
    var target = args.target ? (Array.isArray(args.target) ? args.target.join(", ") : args.target) : ""
    if (step.kind === "key") {
        var verb = { press: "Press", hold: "Hold", release: "Let go of" }[args.verb] || args.verb
        return verb + " " + (args.keys || []).map(function (one) { return one.toUpperCase() }).join(" + ")
    }
    if (step.kind === "write") return "Type “" + (args.text || "") + "”"
    if (step.kind === "wait") return "Wait " + (args.seconds || 0) + " s"
    if (step.kind === "tape") return "Play the recording from " + (args.start || 0) + " to " + (args.end === null || args.end === undefined ? "the end" : args.end + " s")
    if (step.kind === "check") return (args.verb === "until gone" ? "Wait until " + target + " is gone" : "Wait for " + target) + (args.timeout ? " (up to " + args.timeout + " s)" : "")
    if (step.kind === "mouse") {
        var verbs = { click: "Click", right_click: "Right-click", double_click: "Double-click", hover: "Move to", scroll: "Scroll", move_by: "Move the mouse by", mouse_down: "Press the mouse on", mouse_up: "Let go of the mouse" }
        if (args.verb === "scroll") return "Scroll " + (args.notches > 0 ? "up " : "down ") + Math.abs(args.notches || 0)
        if (args.verb === "move_by") return "Move the mouse by " + (args.dx || 0) + ", " + (args.dy || 0)
        return (verbs[args.verb] || args.verb) + (target ? " " + target : "")
    }
    if (step.kind === "if") return "If " + (args.spot || args.condition || "…")
    if (step.kind === "loop") return args.times !== undefined ? "Repeat " + args.times + " times" : "Repeat until " + (args.until || "…")
    if (step.kind === "call") return (args.action ? "Do the action " : "Call ") + (args.name || "")
    return step.source || step.kind
}
