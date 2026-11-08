// Words and colours for Scout's record of an image (scout.py's Sighting, as a dict), shared by its pill's forms and
// its boxes on the game.
.pragma library

// the state's colour: seen ok, weak warn, not seen yet faint
function ink(colors, image) {
    if (!image) return colors.faint
    return image.state === "seen" ? colors.ok : image.state === "weak" ? colors.warn : colors.faint
}

function groupLabel(group) {
    return group === "weak" ? "Weak" : group === "not" ? "Not seen yet" : group === "seen" ? "Seen" : "All"
}

// how long ago, in a few words
function ago(seconds) {
    if (seconds < 5) return "now"
    if (seconds < 60) return Math.round(seconds) + " s ago"
    if (seconds < 3600) return Math.round(seconds / 60) + " min ago"
    return Math.round(seconds / 3600) + " h ago"
}

// one line of where and how well it was seen: "seen on Shop now · best 0.86, needs 0.90"
function seenLine(image, now) {
    if (!image) return ""
    if (image.state === "not") return "not seen yet · its screen: " + image.screen
    return "seen on " + image.seenOn + " " + ago(now - image.seenAt) + " · best " + image.best.toFixed(2)
        + ", needs " + image.needs.toFixed(2)
}

// what's wrong with it, and what to do: "" for one seen
function problem(image) {
    if (!image) return ""
    if (image.state === "not") return "not seen yet: show it its screen, or retake it on the screen now"
    if (image.alike.length > 0)
        return "looks like " + image.alike.join(", ") + " on the same spot: retake it tighter, or with colour"
    if (image.best < image.needs)
        return image.needs - image.best < 0.05 ? "a little under what it needs: retake it where it was seen"
            : "under what it needs: retake it where it was seen"
    return ""
}

// the short reason under its name in a list
function shortReason(image) {
    if (!image || image.state !== "weak") return ""
    if (image.alike.length > 0) return "looks like " + image.alike[0]
    return "needs " + image.needs.toFixed(2)
}
