// Capture: the frozen screen, full screen. A target is an image, the region it's searched in and the location to
// click, made together. The kind chosen in the pill (1, 2, 3 or Tab) is what a click or drag makes and what the handles
// and arrows change: click to box an image or region (again for bigger, right-click smaller) or drag one, drag its edges
// and corners to resize it, click the location. The pill is the shared one (PillBody): docked on an edge it slides
// out of sight a few seconds after the mouse leaves it and the edge brings it back; it can be dragged to another edge
// or into the middle to float. Ctrl+Z / Ctrl+Y undo and redo; T tests; Enter saves. Taking new targets
// (capture.several), several are taken on the shot: a box away from the active one starts another, a click on one makes
// it active, N / Shift+N step through them; Test and Save take them all.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Shapes
import QtQuick.Window

Window {
    id: shotWindow
    visibility: capture.isOpen ? Window.FullScreen : Window.Hidden
    transientParent: null  // its own window: it shows while the Studio is hidden (Windows hides a hidden window's tool windows too)
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "black"
    title: "darbit Capture"

    // the target, in the shot's pixels: [x, y, w, h] boxes and an [x, y] location, each null until made
    property var image: null
    property var region: null
    property var location: null
    property string regionName: ""       // the shared region picked from the bot's (its box is `region`); "" for its own
    property bool linking: false         // a shared region going in: changing `region` otherwise makes it the image's own
    property var regionChoices: []       // the bot's regions to pick from: shared ones, then other images' own
    property var previewRegion: null     // the region under the mouse in the picker
    property bool regionsOpen: false     // the picker is open (its own flag: a child of a hidden item reads as hidden)
    property string tool: "image"        // the kind being made and changed: image, region or location
    property var past: []                // undo: the target as it was before each change
    property var future: []              // redo
    property double nudgedAt: 0          // a burst of arrow presses is one undo step
    property var saved: ({})             // what a retaken target already has: region, offset, location, picture
    property var boxes: []               // the candidates around the last click, smallest first
    property int chosen: 0
    property var lastClick: null
    property var matches: []
    property var waiting: null           // Test's answer while the scan sweeps the searched region
    property real similarity: 0.9        // after Test: matches under it fade
    // the targets on this shot (several when taking new ones, capture.several): each { name, image, region,
    // regionName, location, test }. The active one is edited through image, region, location and the name field;
    // its entry here is brought up to date (sync) before the list is read or another one is made active
    property var targets: [blank("")]
    property int active: 0
    property int hovered: -1             // the target under the mouse: its name shows
    // what's on the shot, the active one as it is now: { index, name, kind, box, ... } for each with something made,
    // with what Test found (scoreText, scoreShort for a narrow tile, scoreTone; "" before Test)
    readonly property var shown: {
        var list = []
        for (var index = 0; index < targets.length; index++) {
            var target = index === active ? live() : targets[index]
            if (!hasParts(target)) continue
            var found = target.image ? verdict(target) : null
            list.push(Object.assign({
                index: index, kind: kindOfTarget(target), box: mainBox(target),
                scoreText: found ? verdictText(found) : "", scoreShort: found ? verdictShort(found) : "", scoreTone: found ? verdictTone(found) : "plain"
            }, target))
        }
        return list
    }
    property bool listOpen: true         // the pill's tiles of the targets on this shot are open
    property string note: ""
    property bool noteBad: false
    // the pill slid out of sight past its edge (captureHiding, hiding.py; never while floating or dragged)
    readonly property bool tucked: captureHiding.tucked && !capturePlace.floating && !capturePlace.dragging
    readonly property bool stacked: pillZone.form !== "row"  // the pill is a column (a side edge) or floating
    readonly property bool compact: capture.several && stacked  // several targets in a column: tiles, glyph rows
    property bool comparing: false       // C held: the saved image over the new one
    property bool gliding: false         // a click stepped to a bigger or smaller box: it glides there
    readonly property real scale: Math.min(width / Math.max(1, capture.shotWidth), height / Math.max(1, capture.shotHeight))
    readonly property var current: capture.items.length > 0 ? capture.items[0] : null
    readonly property string kind: image ? "image" : region ? "region" : location ? "location" : ""
    // where an image is searched: the whole screen, a shared region (a place of its own that several images name), or
    // a region of its own
    readonly property string searchIn: !region ? "screen" : regionName ? "shared" : "own"
    readonly property var box: image     // the image, by its old name
    readonly property var kinds: ["image", "region", "location"]
    readonly property color imageInk: studio.colors.kindImage
    readonly property color regionInk: studio.colors.kindRegion
    readonly property color locationInk: studio.colors.kindLocation
    readonly property color solid: studio.colors.solid

    onVisibleChanged: if (visible) { stopHolding(); shutter.flash(); reset(); nameField.text = current ? current.name : ""; takeSaved(nameField.text); stage.forceActiveFocus(); showPill() }
    onCurrentChanged: if (current && visible) { nameField.text = current.name; tool = kindOf(current.kind) }
    onRegionChanged: if (!linking) regionName = ""

    function kindOf(name) { return name === "region" ? "region" : name === "location" || name === "point" ? "location" : "image" }
    function inkOf(name) { return name === "region" ? regionInk : name === "location" ? locationInk : imageInk }

    // ---- the targets on the shot
    function blank(name) { return { name: name, image: null, region: null, regionName: "", location: null, test: null } }
    function hasParts(target) { return !!target && (!!target.image || !!target.region || !!target.location) }
    function kindOfTarget(target) { return target.image ? "image" : target.region ? "region" : target.location ? "location" : "" }
    // the box a target is clicked by: its image, else its region, else a little square around its location
    function mainBox(target) {
        if (target.image) return target.image
        if (target.region) return target.region
        if (target.location) return [target.location[0] - 8, target.location[1] - 8, 16, 16]
        return null
    }
    function within(box, at) { return !!box && at[0] >= box[0] && at[0] <= box[0] + box[2] && at[1] >= box[1] && at[1] <= box[1] + box[3] }
    // the active target as it is now
    function live() {
        var kept = targets[active]
        return { name: nameField.text.trim(), image: image, region: region, regionName: regionName, location: location, test: kept ? kept.test : null }
    }
    function sync() { var list = targets.slice(); list[active] = live(); targets = list }
    function load(target) {
        linking = true; image = target.image; region = target.region; regionName = target.regionName || ""; linking = false
        location = target.location; nameField.text = target.name; matches = []
    }
    // a name to start with, the way SikuliX names a capture: the time, in ms (one more if a box here has it already)
    function autoName() {
        var taken = {}
        for (var index = 0; index < targets.length; index++) taken[targets[index].name] = true
        taken[nameField.text.trim()] = true
        var stamp = Date.now()
        while (taken[String(stamp)]) stamp++
        return String(stamp)
    }
    function nameIfNew() { if (capture.several && !nameField.text.trim()) nameField.text = autoName() }
    // the target under `at` (shot pixels) other than the active one, the smallest when they overlap; -1 for none
    function targetAt(at) {
        var found = -1, smallest = Infinity
        for (var index = 0; index < shown.length; index++) {
            var entry = shown[index]
            if (entry.index === active || !within(entry.box, at)) continue
            if (entry.box[2] * entry.box[3] < smallest) { smallest = entry.box[2] * entry.box[3]; found = entry.index }
        }
        return found
    }
    // a new box of `part` away from the active target starts another target when it would replace that target's own
    // kind (an image's image), not when it adds to it (an image's region or location)
    function startsNew(part, at) {
        if (!capture.several) return false
        var own = kindOfTarget(live())
        if (!own || within(mainBox(live()), at)) return false
        return part === own || (own === "region" && part === "location") || (own === "location" && part === "region")
    }
    // another target, empty, to make with the kind picked; the active one is kept if it has anything
    function newTarget() {
        sync()
        var list = targets.slice()
        if (!hasParts(list[active])) list.splice(active, 1)
        list.push(blank(""))
        targets = list; active = list.length - 1
        load(list[active])
        nameField.text = autoName()
        boxes = []; lastClick = null
    }
    function addTarget() {
        if (!capture.several) return
        newTarget()
        say("A new target: click or drag it on the screen", false)
    }
    // make the target at `index` the one edited: the name field, the kind, the handles and the arrows act on it
    function activate(index) {
        if (index === active || index < 0 || index >= targets.length) return
        sync()
        var list = targets.slice(), target = list[index]
        if (!hasParts(list[active])) { list.splice(active, 1); if (index > active) index-- }
        targets = list; active = index
        load(target)
        tool = kindOfTarget(target) || tool
        boxes = []; lastClick = null; regionsOpen = false
    }
    // N and Shift+N: the next or the previous target on the shot
    function step(by) {
        var count = shown.length
        if (count === 0) return
        var at = -1
        for (var index = 0; index < count; index++) if (shown[index].index === active) at = index
        var next = at < 0 ? (by > 0 ? 0 : count - 1) : (at + by + count) % count
        activate(shown[next].index)
        stage.forceActiveFocus()
    }
    // drop the target at `index` from the shot (an undo step)
    function removeTarget(index) {
        if (index < 0 || index >= targets.length) return
        remember()
        sync()
        var list = targets.slice()
        list.splice(index, 1)
        if (list.length === 0) list.push(blank(""))
        var next = index === active ? Math.min(index, list.length - 1) : index < active ? active - 1 : active
        targets = list; active = next
        load(list[next])
    }
    // Esc with nothing picked: an empty new target goes back to the last one taken, else Capture closes
    function back() {
        if (partOf(tool)) { drop(tool); return }
        if (capture.several && !hasParts(live()) && shown.length > 0) { activate(shown[shown.length - 1].index); return }
        capture.close()
    }

    // ---- the target and its history
    function snapshot() {
        return { image: image, region: region, regionName: regionName, location: location, targets: targets, active: active, name: nameField.text }
    }
    function restore(state) {
        var moved = state.active !== active || state.targets.length !== targets.length
        targets = state.targets; active = state.active
        linking = true; image = state.image; region = state.region; regionName = state.regionName || ""; linking = false
        location = state.location; matches = []
        if (moved) nameField.text = state.name  // a name typed into the same target stays
    }
    // a region the bot has already: shared by name (moving it later moves every image in it), or another image's own
    function useRegion(entry) {
        remember()
        linking = true; region = entry.region; regionName = entry.name || ""; linking = false
        tool = "region"; matches = []; previewRegion = null; regionsOpen = false
        say(entry.name ? "Searched in " + entry.name + ", shared" : "Searched where " + entry.used_by.join(", ") + " are", false)
    }
    function openRegions() {
        regionChoices = capture.regions()
        regionsOpen = !regionsOpen
    }
    function searchOn(where) {
        if (where === "screen") { if (region) setPart("region", null); regionsOpen = false; say("Searched on the whole screen", false) }
        else if (where === "shared") openRegions()
        else {
            regionsOpen = false
            if (regionName) { remember(); regionName = ""; say("Its own copy of the region now: changing it changes only this image", false) }
            else if (!region) { tool = "region"; say("Drag the region only this image is searched in", false) }
        }
    }
    // the region drawn becomes a shared one, saved under its own name, and the image names it
    function shareRegion(name) {
        name = name.trim()
        if (!region || !name) { say("Draw the region and name it first", true); return }
        var result = capture.save(name, "region", null, region, null, "")
        if (result.error) { say(result.error, true); return }
        linking = true; regionName = name; linking = false
        regionsOpen = false
        say(name + " saved as a shared region: other images can be searched in it too", false)
    }
    function remember() { past = past.concat([snapshot()]).slice(-200); future = [] }
    function undo() {
        if (!past.length) { say("Nothing to undo", false); return }
        future = future.concat([snapshot()])
        restore(past[past.length - 1]); past = past.slice(0, -1)
    }
    function redo() {
        if (!future.length) { say("Nothing to redo", false); return }
        past = past.concat([snapshot()])
        restore(future[future.length - 1]); future = future.slice(0, -1)
    }
    function setPart(part, value) {
        remember()
        put(part, value)
    }
    // a part of the active target, without an undo step of its own
    function put(part, value) {
        if (value) nameIfNew()
        if (part === "image") {
            image = value
            // a retake keeps where it clicked, from the new image's centre
            if (value && !location && saved.offset) location = [value[0] + value[2] / 2 + saved.offset[0], value[1] + value[3] / 2 + saved.offset[1]]
        } else if (part === "region") region = value
        else location = value
        tool = part
        matches = []
    }
    function partOf(name) { return name === "image" ? image : name === "region" ? region : location }
    function drop(name) { if (partOf(name)) setPart(name, null) }
    function choose(name) { tool = name; if (name !== "region") regionsOpen = false; stage.forceActiveFocus() }
    function reset() {
        image = null; region = null; location = null; past = []; future = []; saved = ({})
        targets = [blank("")]; active = 0; hovered = -1
        regionName = ""; previewRegion = null; regionsOpen = false
        boxes = []; matches = []; waiting = null; note = ""; lastClick = null
        tool = current ? kindOf(current.kind) : "image"
    }
    // a retake: the target's saved region and location come back, and its image is there to compare with
    function takeSaved(name) {
        saved = name ? capture.existing(name) : ({})
        // an image boxed before its name was typed: its saved location goes on from the new image's centre
        if (image && !location && saved.offset) location = [image[0] + image[2] / 2 + saved.offset[0], image[1] + image[3] / 2 + saved.offset[1]]
        if (saved.region && !region) { linking = true; region = saved.region; regionName = saved.region_name || ""; linking = false }
        if (saved.location && !location) location = saved.location
        if (saved.needs) similarity = saved.needs  // Test's line: what the bot needs for it
    }

    function toShot(x, y) { return [Math.round(x / scale), Math.round(y / scale)] }
    function clamp(next) {
        var x = Math.max(0, Math.min(next[0], capture.shotWidth - 1)), y = Math.max(0, Math.min(next[1], capture.shotHeight - 1))
        return [x, y, Math.max(1, Math.min(next[2], capture.shotWidth - x)), Math.max(1, Math.min(next[3], capture.shotHeight - y))]
    }
    function say(text, bad) { note = text; noteBad = !!bad; if (text) { showPill(); noteTimer.restart() } }
    function inside(outer, inner) { return outer[0] <= inner[0] && outer[1] <= inner[1] && outer[0] + outer[2] >= inner[0] + inner[2] && outer[1] + outer[3] >= inner[1] + inner[3] }

    // a click with the image or region tool: the box around it, or the next bigger (left) or smaller (right) one on a
    // click at the same spot; with the location tool, the location
    // Taking new targets, a click away from the active one that would replace its own kind starts another target.
    function clicked(x, y, bigger) {
        var at = toShot(x, y)
        var same = lastClick && Math.abs(lastClick[0] - at[0]) < 4 && Math.abs(lastClick[1] - at[1]) < 4
        var fresh = !same && startsNew(tool, at)
        if (fresh) { remember(); newTarget() }
        if (tool === "location") { if (fresh) put("location", at); else setPart("location", at); return }
        if (!same) {
            var found = capture.candidates(at[0], at[1], tool)
            boxes = found.boxes; chosen = found.start || 0; lastClick = at
        } else if (boxes.length) {
            chosen = Math.max(0, Math.min(boxes.length - 1, chosen + (bigger ? 1 : -1)))
        }
        if (!boxes.length) return
        gliding = !fresh; glideTimer.restart()
        if (fresh) put(tool, boxes[chosen]); else setPart(tool, boxes[chosen])
    }
    Timer { id: glideTimer; interval: 220; onTriggered: shotWindow.gliding = false }
    // an arrow held: a press moves or resizes 1 px (Shift: 10) and stays exact; held for half a second, it speeds up
    // to a top speed until let go
    property var held: null              // the arrow held: its key, direction, step and when it went down
    readonly property int holdDelay: 500     // ms before a held arrow speeds up
    readonly property int holdRamp: 1500     // ms from its first speed to the top one
    readonly property int holdTop: 900       // px a second
    function pressArrow(key, dx, dy, step, grow) {
        nudge(dx * step, dy * step, grow)
        held = { key: key, dx: dx, dy: dy, step: step, grow: grow, since: Date.now(), last: Date.now(), carry: 0 }
        holding.restart()
    }
    function releaseArrow(key) { if (held && held.key === key) stopHolding() }
    function stopHolding() { held = null; holding.stop() }
    // an arrow key's direction, or null for another key
    function arrowOf(key) {
        if (key === Qt.Key_Left) return [-1, 0]
        if (key === Qt.Key_Right) return [1, 0]
        if (key === Qt.Key_Up) return [0, -1]
        if (key === Qt.Key_Down) return [0, 1]
        return null
    }
    // px a second, `ms` after the arrow went down: none before the delay, then from 30 a step up to the top speed
    function holdSpeed(ms, step) {
        if (ms < holdDelay) return 0
        var first = 30 * step
        return Math.min(holdTop, first + (holdTop - first) * (ms - holdDelay) / holdRamp)
    }
    function keepNudging() {
        if (!held) { holding.stop(); return }
        var now = Date.now()
        var moved = holdSpeed(now - held.since, held.step) * (now - held.last) / 1000 + held.carry
        var whole = Math.floor(moved)
        held.last = now; held.carry = moved - whole
        if (whole > 0) nudge(held.dx * whole, held.dy * whole, held.grow)
    }
    Timer { id: holding; interval: 16; repeat: true; onTriggered: shotWindow.keepNudging() }
    // a box's corners and edges, clockwise from the top left, as fractions of its width and height
    readonly property var gripX: [0, 0.5, 1, 1, 1, 0.5, 0, 0]
    readonly property var gripY: [0, 0, 0, 0.5, 1, 1, 1, 0.5]
    // `box` with the corner or edge at (fx, fy) dragged to the shot pixel `p`: the other sides stay, and it keeps 1 px
    function resized(box, fx, fy, p) {
        var left = box[0], top = box[1], right = box[0] + box[2], bottom = box[1] + box[3]
        if (fx === 0) left = Math.min(p[0], right - 1)
        if (fx === 1) right = Math.max(p[0], left + 1)
        if (fy === 0) top = Math.min(p[1], bottom - 1)
        if (fy === 1) bottom = Math.max(p[1], top + 1)
        left = Math.max(0, left); top = Math.max(0, top)
        return clamp([left, top, right - left, bottom - top])
    }
    function nudge(dx, dy, grow) {
        var part = partOf(tool)
        if (!part) return
        if (Date.now() - nudgedAt > 700) remember()
        nudgedAt = Date.now()
        if (tool === "location") location = [Math.max(0, Math.min(capture.shotWidth - 1, part[0] + dx)), Math.max(0, Math.min(capture.shotHeight - 1, part[1] + dy))]
        else {
            var next = clamp(grow ? [part[0], part[1], part[2] + dx, part[3] + dy] : [part[0] + dx, part[1] + dy, part[2], part[3]])
            if (tool === "image") image = next; else region = next
        }
        matches = []
    }

    function test() {
        if (capture.several) { testAll(); return }
        if (!image) { say("Box an image first", true); return }
        var found = capture.test(image, region)
        if (found.error) { say(found.error, true); return }
        matches = []
        note = ""
        waiting = found
        if (studio.effects && found.searched) scan.sweep(found.searched)
        else showFound()
    }
    // what Test found: the image itself counts once; look-alikes are the other places, scoring under the line
    // Test with several targets: every image on the shot, each in its own region; each keeps its matches (test)
    function testAll() {
        sync()
        var list = targets.slice(), tested = 0
        for (var index = 0; index < list.length; index++) {
            var target = list[index]
            if (!target.image) continue
            var found = capture.test(target.image, target.region)
            if (found.error) { say(found.error, true); return }
            list[index] = Object.assign({}, target, { test: { image: target.image.join(), region: String(target.region), ms: found.ms, matches: found.matches || [] } })
            tested++
        }
        if (!tested) { say("Box an image first", true); return }
        targets = list
        matches = []
        note = ""
        waiting = { all: true }
        if (studio.effects) scan.sweep([0, 0, capture.shotWidth, capture.shotHeight])
        else showFound()
    }
    // what Test found for a target, if it was tested as it is now: how many places score over the line, its own score
    // and the look-alikes (the other places, under the line); null when it wasn't
    function verdict(target) {
        var test = target.test
        if (!test || !target.image || test.image !== target.image.join() || test.region !== String(target.region)) return null
        var own = null, others = [], alike = [], strong = 0
        for (var index = 0; index < test.matches.length; index++) {
            var match = test.matches[index]
            if (match.score >= similarity) strong++
            if (!own && Math.abs(match.x - target.image[0]) <= 3 && Math.abs(match.y - target.image[1]) <= 3) own = match
            else { others.push(match); if (match.score < similarity) alike.push(match) }
        }
        return { strong: strong, score: own ? own.score : 0, others: others, alike: alike, best: alike.length ? alike[0].score : 0 }
    }
    // a verdict in a few words and its tone, for the chip on its box (and its tile)
    function verdictText(found) {
        if (found.strong === 0) return "not found"
        if (found.strong > 1) return "found " + found.strong + "×"
        if (found.alike.length) return found.best.toFixed(2) + " · " + found.alike.length + " alike"
        return found.score.toFixed(2) + " ✓"
    }
    function verdictShort(found) {
        if (found.strong === 0) return "none"
        if (found.strong > 1) return found.strong + "×"
        return (found.alike.length ? found.best : found.score).toFixed(2)
    }
    function verdictTone(found) { return found.strong === 0 ? "danger" : found.strong > 1 || found.alike.length ? "warn" : "ok" }
    function showFoundAll() {
        var once = 0, others = [], close = [], ms = 0
        for (var index = 0; index < targets.length; index++) {
            var target = index === active ? live() : targets[index]
            var found = verdict(target)
            if (!found) continue
            ms += target.test.ms
            if (found.strong === 1 && !found.alike.length) once++
            else close.push(target.name)
            others = others.concat(found.others)
        }
        matches = others  // the other places each was found, on the shot
        var told = "Test: " + once + " found once"
        if (close.length) told += " · " + (close.length > 2 ? close.slice(0, 2).join(", ") + " and " + (close.length - 2) + " more" : close.join(", ")) + (close.length === 1 ? " needs" : " need") + " a look"
        var unscored = shown.filter(function (entry) { return !entry.image }).length
        if (unscored) told += " · " + (unscored === 1 ? "a region or location has" : unscored + " regions and locations have") + " no score"
        say(told + " · " + ms + " ms", close.length > 0)
    }
    function showFound() {
        var found = waiting
        waiting = null
        if (!found) return
        if (found.all) { showFoundAll(); return }
        matches = found.matches || []
        var strong = matches.filter(function (match) { return match.score >= shotWindow.similarity }).length
        var others = matches.length - strong
        var where = strong === 0 ? "Not found" : strong === 1 ? "Found once" : "Found " + strong + " times"
        var alike = others === 0 ? "nothing else close" : others === 1 ? "1 look-alike under the line" : others + " look-alikes under the line"
        say(where + " at " + shotWindow.similarity.toFixed(2) + (region ? " in its region" : " on the whole screen") + " · " + alike + " · " + found.ms + " ms", strong !== 1)
    }
    // Save with several targets: every one on the shot, in the order taken. The first that can't be saved stops it,
    // made active with the reason; the ones saved are gone from the shot
    function saveAll() {
        sync()
        var names = {}
        for (var index = 0; index < targets.length; index++) {
            var target = targets[index]
            if (!hasParts(target)) continue
            if (!target.name) { activate(index); say("Give it a name first", true); nameField.forceActiveFocus(); return }
            if (names[target.name]) { activate(index); say("Two targets are called " + target.name + ": rename one", true); nameField.forceActiveFocus(); return }
            names[target.name] = true
        }
        var left = targets.slice(), count = 0, told = "", bad = false
        while (left.length) {
            target = left[0]
            if (!hasParts(target)) { left.shift(); continue }
            var result = capture.save(target.name, kindOfTarget(target), target.image, target.region, target.location, target.image && target.region ? target.regionName : "")
            if (result.error) {
                targets = left; active = 0; load(left[0]); tool = kindOfTarget(left[0]) || tool
                say(result.error, true)
                return
            }
            left.shift()
            count++
            savedPulse.show(mainBox(target))
            if (result.risky) { told = result.said; bad = true }
            else if (!bad) told = count === 1 ? result.said : "Saved " + count + " targets"
        }
        if (!count) { say("Make an image, a region or a location first", true); return }
        if (!bad && count > 1) told = "Saved " + count + " targets"
        reset()
        nameField.text = ""
        say(told, bad)
        if (capture.items.length === 0) { studio.say(told); closing.restart() }
    }
    function save() {
        if (capture.several) { saveAll(); return }
        var name = nameField.text.trim()
        if (!kind) { say("Make an image, a region or a location first", true); return }
        var result = capture.save(name, kind, image, region, location, image && region ? regionName : "")
        if (result.error) { say(result.error, true); return }
        var told = result.said || ("Saved " + name), bad = !!result.risky
        savedPulse.show(image || region || (location ? [location[0] - 10, location[1] - 10, 20, 20] : null))
        reset()
        nameField.text = current ? current.name : ""
        takeSaved(nameField.text)
        say(told, bad)
        // nothing left to take (a retake, or one target): Capture closes once the save has shown, and the Studio says it
        if (capture.items.length === 0) { studio.say(told); closing.restart() }
    }
    Timer { id: closing; interval: studio.effects ? 520 : 0; onTriggered: capture.close() }

    // a key's name, for the pill's ‹ N › (the arrows beside it carry the tips)
    component KeyCap: Rectangle {
        property alias text: capLabel.text
        implicitWidth: Math.max(22, capLabel.implicitWidth + 10); implicitHeight: 22
        radius: 6
        color: "transparent"; border.color: studio.colors.line
        Layout.alignment: Qt.AlignVCenter
        Text { id: capLabel; anchors.centerIn: parent; color: studio.colors.muted; font.pixelSize: 11; font.weight: Font.DemiBold }
    }
    // the targets on this shot as a stack: their first images fanned out, how many, and ▴ to fold the tiles away (▾ to
    // open them)
    component StackToggle: Rectangle {
        id: stack
        objectName: "targetStack"
        readonly property int count: shotWindow.shown.length
        implicitWidth: stackLine.implicitWidth + 20; implicitHeight: shotWindow.stacked ? 34 : 40
        radius: height / 2
        color: stackArea.containsMouse && count > 0 ? studio.colors.raisedHover : studio.colors.raised
        border.color: studio.colors.line
        Row {
            id: stackLine
            anchors.verticalCenter: parent.verticalCenter
            x: shotWindow.stacked ? 12 : 10
            spacing: 8
            Item {  // up to four of their images, overlapping
                visible: stack.count > 0
                width: 22 + (Math.min(4, stack.count) - 1) * 12; height: 18
                anchors.verticalCenter: parent.verticalCenter
                Repeater {
                    model: shotWindow.shown.slice(0, 4)
                    delegate: Rectangle {
                        required property var modelData
                        required property int index
                        x: index * 12; width: 22; height: 18; radius: 5; clip: true
                        color: "black"; border.color: shotWindow.inkOf(modelData.kind)
                        Image {
                            anchors.fill: parent; anchors.margins: 1
                            source: capture.source ? capture.source + "/" + modelData.box.map(Math.round).join(",") : ""
                            fillMode: Image.PreserveAspectCrop
                        }
                    }
                }
            }
            Text {
                text: (stack.count === 0 ? "None" : stack.count) + " on this shot"
                color: stack.count > 0 ? studio.colors.text : studio.colors.faint
                font.pixelSize: shotWindow.stacked ? 11 : 13; font.weight: Font.DemiBold
                font.capitalization: shotWindow.stacked ? Font.AllUppercase : Font.MixedCase
                font.letterSpacing: shotWindow.stacked ? 0.6 : 0
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                visible: stack.count > 0
                text: shotWindow.listOpen ? "▴" : "▾"
                color: studio.colors.muted; font.pixelSize: 12; font.family: studio.symbols
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        MouseArea {
            id: stackArea
            anchors.fill: parent; hoverEnabled: true
            enabled: stack.count > 0
            cursorShape: Qt.PointingHandCursor
            onClicked: { shotWindow.listOpen = !shotWindow.listOpen; stage.forceActiveFocus() }
        }
        ToolTip.visible: stackArea.containsMouse
        ToolTip.text: shotWindow.listOpen ? "Fold the targets away" : "Show the targets on this shot"
        ToolTip.delay: 400
    }

    // ---- the pill's hiding, and its messages fading
    function showPill() { captureHiding.show() }
    Timer { id: noteTimer; interval: 5000; onTriggered: shotWindow.note = "" }

    Item {
        id: stage
        anchors.fill: parent
        focus: true
        // the mouse at `p` (stage pixels): the magnifier follows it, and the pill comes back at its edge. Called by
        // the hover handler and by the drawing area, which takes the mouse from it while pressed and after a click
        function follow(p) {
            captureHiding.moveTo(Math.round(p.x), Math.round(p.y))
            shotWindow.hovered = capture.several ? shotWindow.targetAt(shotWindow.toShot(p.x, p.y)) : -1
            if (magnifier.pinned) return
            magnifier.hoverPoint = Qt.point(p.x, p.y)
            // the pixel the mouse is on, not the nearest corner
            magnifier.at = Qt.point(Math.min(capture.shotWidth - 1, Math.floor(p.x / shotWindow.scale)),
                                    Math.min(capture.shotHeight - 1, Math.floor(p.y / shotWindow.scale)))
        }
        Keys.onPressed: function (event) {
            var step = (event.modifiers & Qt.ShiftModifier) ? 10 : 1
            var control = (event.modifiers & Qt.ControlModifier) !== 0
            var arrow = shotWindow.arrowOf(event.key)
            if (event.key === Qt.Key_Escape) shotWindow.back()
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) shotWindow.save()
            else if (control && event.key === Qt.Key_Z && (event.modifiers & Qt.ShiftModifier)) shotWindow.redo()
            else if (control && event.key === Qt.Key_Z) shotWindow.undo()
            else if (control && event.key === Qt.Key_Y) shotWindow.redo()
            else if (event.key === Qt.Key_1) shotWindow.choose("image")
            else if (event.key === Qt.Key_2) shotWindow.choose("region")
            else if (event.key === Qt.Key_3) shotWindow.choose("location")
            else if (event.key === Qt.Key_Tab) shotWindow.choose(shotWindow.kinds[(shotWindow.kinds.indexOf(shotWindow.tool) + 1) % 3])
            else if (event.key === Qt.Key_T) shotWindow.test()
            else if (event.key === Qt.Key_N) shotWindow.step((event.modifiers & Qt.ShiftModifier) ? -1 : 1)
            else if (event.key === Qt.Key_A) shotWindow.addTarget()
            else if (event.key === Qt.Key_Delete || event.key === Qt.Key_Backspace) shotWindow.drop(shotWindow.tool)
            else if (event.key === Qt.Key_Z) magnifier.pinned = !magnifier.pinned
            else if (event.key === Qt.Key_C && !event.isAutoRepeat) shotWindow.comparing = true
            else if (arrow) { if (!event.isAutoRepeat) shotWindow.pressArrow(event.key, arrow[0], arrow[1], step, control) }  // held: a timer moves it
            else return
            event.accepted = true
        }
        Keys.onReleased: function (event) {
            if (event.isAutoRepeat) return
            if (event.key === Qt.Key_C) shotWindow.comparing = false
            shotWindow.releaseArrow(event.key)
        }
        onActiveFocusChanged: if (!activeFocus) shotWindow.stopHolding()  // the arrow's release would go elsewhere

        Image {
            id: shot
            source: capture.source
            cache: false  // gone when Capture closes: a whole screen stays in Qt's cache otherwise
            width: capture.shotWidth * shotWindow.scale; height: capture.shotHeight * shotWindow.scale
            smooth: true
        }

        // the shot outside the image, dimmed (the design system's screen-dim)
        Item {
            id: dim
            visible: !!shotWindow.image
            readonly property var b: shotWindow.image ? shotWindow.image.map(function (v) { return Math.round(v * shotWindow.scale) }) : [0, 0, 0, 0]
            anchors.fill: shot
            Rectangle { color: Qt.rgba(0, 0, 0, 0.5); x: 0; y: 0; width: dim.width; height: dim.b[1] }
            Rectangle { color: Qt.rgba(0, 0, 0, 0.5); x: 0; y: dim.b[1] + dim.b[3]; width: dim.width; height: dim.height - y }
            Rectangle { color: Qt.rgba(0, 0, 0, 0.5); x: 0; y: dim.b[1]; width: dim.b[0]; height: dim.b[3] }
            Rectangle { color: Qt.rgba(0, 0, 0, 0.5); x: dim.b[0] + dim.b[2]; y: dim.b[1]; width: dim.width - x; height: dim.b[3] }
        }

        // a click or a drag makes the chosen kind; a drag that starts inside it moves it
        MouseArea {
            id: drawing
            anchors.fill: shot
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            hoverEnabled: true  // the mouse's moves reach the magnifier through here too (stage.follow)
            property var from: null
            property bool dragged: false
            property var moving: null  // the chosen box and the shot pixel the drag started at
            property bool picked: false  // the press made another target active: no new box on release
            onPressed: function (mouse) {
                from = [mouse.x, mouse.y]; dragged = false; moving = null; stage.forceActiveFocus()
                var at = shotWindow.toShot(mouse.x, mouse.y)
                var other = shotWindow.targetAt(at)
                picked = other >= 0
                if (picked) shotWindow.activate(other)
                var part = shotWindow.tool !== "location" ? shotWindow.partOf(shotWindow.tool) : null
                if (part && at[0] >= part[0] && at[0] <= part[0] + part[2] && at[1] >= part[1] && at[1] <= part[1] + part[3])
                    moving = { box: part.slice(), at: at }
            }
            onPositionChanged: function (mouse) {
                stage.follow(mapToItem(stage, mouse.x, mouse.y))
                if (!from || mouse.buttons !== Qt.LeftButton) return
                if (!dragged && Math.abs(mouse.x - from[0]) + Math.abs(mouse.y - from[1]) < 6) return
                if (!dragged) {
                    shotWindow.remember()
                    // a box drawn away from the active target, of its own kind: another target
                    if (!moving && shotWindow.startsNew(shotWindow.tool, shotWindow.toShot(from[0], from[1]))) shotWindow.newTarget()
                    if (!moving) shotWindow.nameIfNew()
                }
                dragged = true
                shotWindow.matches = []
                var at = shotWindow.toShot(mouse.x, mouse.y)
                if (shotWindow.tool === "location") { shotWindow.location = at; return }
                if (moving) {
                    var moved = shotWindow.clamp([moving.box[0] + at[0] - moving.at[0], moving.box[1] + at[1] - moving.at[1], moving.box[2], moving.box[3]])
                    if (shotWindow.tool === "image") shotWindow.image = moved; else shotWindow.region = moved
                    return
                }
                var a = shotWindow.toShot(Math.min(from[0], mouse.x), Math.min(from[1], mouse.y))
                var b = shotWindow.toShot(Math.max(from[0], mouse.x), Math.max(from[1], mouse.y))
                var drawn = shotWindow.clamp([a[0], a[1], b[0] - a[0], b[1] - a[1]])
                if (shotWindow.tool === "region") shotWindow.region = drawn; else shotWindow.image = drawn
                shotWindow.boxes = []; shotWindow.lastClick = null
            }
            onReleased: function (mouse) {
                if (!dragged && !picked) shotWindow.clicked(mouse.x, mouse.y, mouse.button === Qt.LeftButton)
                from = null; moving = null; picked = false
            }
        }

        // a box (the image or its region), with handles while its kind is the one chosen
        component PartBox: Rectangle {
            id: partBox
            property string part: "image"
            property var value: null
            readonly property color ink: shotWindow.inkOf(part)
            readonly property var b: value || [0, 0, 0, 0]
            readonly property bool chosen: shotWindow.tool === part
            visible: !!value
            x: b[0] * shotWindow.scale; y: b[1] * shotWindow.scale
            width: b[2] * shotWindow.scale; height: b[3] * shotWindow.scale
            Behavior on x { enabled: shotWindow.gliding && studio.effects; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            Behavior on y { enabled: shotWindow.gliding && studio.effects; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            Behavior on width { enabled: shotWindow.gliding && studio.effects; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            Behavior on height { enabled: shotWindow.gliding && studio.effects; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
            color: chosen ? Qt.rgba(ink.r, ink.g, ink.b, 0.06) : "transparent"
            border.color: part === "region" ? "transparent" : ink; border.width: chosen ? 2 : 1
            opacity: chosen ? 1 : 0.6
            // a region's outline: dashes that march while it's the kind picked
            Shape {
                visible: partBox.part === "region"
                anchors.fill: parent
                ShapePath {
                    strokeColor: partBox.ink; strokeWidth: partBox.chosen ? 2 : 1; fillColor: "transparent"
                    strokeStyle: ShapePath.DashLine; dashPattern: [5, 4]
                    NumberAnimation on dashOffset { running: partBox.chosen && studio.effects && partBox.visible; from: 0; to: -9; duration: 600; loops: Animation.Infinite }
                    startX: 0; startY: 0
                    PathLine { x: partBox.width; y: 0 }
                    PathLine { x: partBox.width; y: partBox.height }
                    PathLine { x: 0; y: partBox.height }
                    PathLine { x: 0; y: 0 }
                }
            }
            // the handles: a square on each corner and edge's middle
            Repeater {
                model: partBox.chosen ? 8 : 0
                delegate: Rectangle {
                    required property int index
                    x: partBox.width * shotWindow.gripX[index] - 5; y: partBox.height * shotWindow.gripY[index] - 5
                    width: 10; height: 10; radius: 2
                    color: "white"; border.color: partBox.ink
                }
            }
            // its edges and corners, dragged to resize it like cropping; the cursor shows which way. The magnifier and
            // the readouts follow, and one drag is one undo step
            Repeater {
                model: partBox.chosen ? 8 : 0
                delegate: MouseArea {
                    id: grip
                    objectName: "grip" + index
                    required property int index
                    readonly property real fx: shotWindow.gripX[index]
                    readonly property real fy: shotWindow.gripY[index]
                    readonly property int outer: 7   // how far it reaches outside the box, and inside it
                    readonly property int inner: 4
                    property var from: null        // the box when the drag started
                    property bool changed: false
                    // an edge runs between the corners
                    x: fx === 0.5 ? inner : partBox.width * fx - (fx === 0 ? outer : inner)
                    y: fy === 0.5 ? inner : partBox.height * fy - (fy === 0 ? outer : inner)
                    width: fx === 0.5 ? Math.max(0, partBox.width - 2 * inner) : outer + inner
                    height: fy === 0.5 ? Math.max(0, partBox.height - 2 * inner) : outer + inner
                    hoverEnabled: true
                    cursorShape: fx === 0.5 ? Qt.SizeVerCursor : fy === 0.5 ? Qt.SizeHorCursor : fx === fy ? Qt.SizeFDiagCursor : Qt.SizeBDiagCursor
                    onPressed: { from = partBox.b.slice(); changed = false; stage.forceActiveFocus() }
                    onReleased: from = null
                    onPositionChanged: function (mouse) {
                        stage.follow(mapToItem(stage, mouse.x, mouse.y))
                        if (!pressed || !from) return
                        var at = mapToItem(shot, mouse.x, mouse.y)
                        var next = shotWindow.resized(from, fx, fy, shotWindow.toShot(at.x, at.y))
                        if (next.join() === partBox.b.join()) return
                        if (!changed) shotWindow.remember()
                        changed = true
                        if (partBox.part === "image") shotWindow.image = next; else shotWindow.region = next
                        shotWindow.matches = []
                    }
                }
            }
        }
        PartBox { part: "region"; value: shotWindow.region }
        Rectangle {  // the bot's region the mouse is on in the picker
            visible: !!shotWindow.previewRegion
            readonly property var b: shotWindow.previewRegion || [0, 0, 0, 0]
            x: b[0] * shotWindow.scale; y: b[1] * shotWindow.scale
            width: b[2] * shotWindow.scale; height: b[3] * shotWindow.scale
            color: Qt.rgba(shotWindow.regionInk.r, shotWindow.regionInk.g, shotWindow.regionInk.b, 0.12)
            border.color: shotWindow.regionInk; border.width: 2; radius: 4
        }
        PartBox { id: imageBox; part: "image"; value: shotWindow.image }

        // the other targets taken on this shot: their box in their kind's colour, quieter than the active one; a click
        // makes one active. A name shows on the one under the mouse, and after Test what it found
        Repeater {
            model: shotWindow.shown
            delegate: Item {
                id: other
                required property var modelData
                readonly property bool isActive: modelData.index === shotWindow.active
                readonly property color ink: shotWindow.inkOf(modelData.kind)
                x: modelData.box[0] * shotWindow.scale; y: modelData.box[1] * shotWindow.scale
                width: modelData.box[2] * shotWindow.scale; height: modelData.box[3] * shotWindow.scale
                Rectangle {  // an image's box
                    visible: !other.isActive && other.modelData.kind === "image"
                    anchors.fill: parent
                    color: "transparent"; border.color: other.ink; border.width: shotWindow.hovered === other.modelData.index ? 2 : 1
                    opacity: 0.75
                }
                Shape {  // a region's dashes
                    visible: !other.isActive && other.modelData.kind === "region"
                    anchors.fill: parent
                    opacity: 0.75
                    ShapePath {
                        strokeColor: other.ink; strokeWidth: shotWindow.hovered === other.modelData.index ? 2 : 1; fillColor: "transparent"
                        strokeStyle: ShapePath.DashLine; dashPattern: [5, 4]
                        startX: 0; startY: 0
                        PathLine { x: other.width; y: 0 }
                        PathLine { x: other.width; y: other.height }
                        PathLine { x: 0; y: other.height }
                        PathLine { x: 0; y: 0 }
                    }
                }
                Item {  // a location's crosshair
                    visible: !other.isActive && other.modelData.kind === "location"
                    anchors.centerIn: parent
                    opacity: 0.75
                    Rectangle { x: -1; y: -9; width: 2; height: 18; color: other.ink }
                    Rectangle { x: -9; y: -1; width: 18; height: 2; color: other.ink }
                }
                Rectangle {  // its name, on the one under the mouse
                    objectName: "boxName"
                    visible: !other.isActive && shotWindow.hovered === other.modelData.index
                    x: 0; y: -height - 4
                    width: tagLine.implicitWidth + 16; height: 22; radius: 6
                    color: shotWindow.solid; border.color: studio.colors.line
                    Row {
                        id: tagLine
                        anchors.centerIn: parent; spacing: 6
                        Rectangle { width: 7; height: 7; radius: 2; color: other.ink; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: other.modelData.name; color: studio.colors.text; font.family: "monospace"; font.pixelSize: 11 }
                    }
                }
                Chip {  // what Test found
                    visible: other.modelData.scoreText !== ""
                    anchors { right: parent.right; bottom: parent.bottom; margins: 3 }
                    height: 20
                    tone: other.modelData.scoreTone
                    text: other.modelData.scoreText
                }
            }
        }

        // faint guide lines through the mouse, across the whole screen
        Rectangle {
            visible: magnifier.at.x >= 0 && !magnifier.pinned
            x: 0; y: magnifier.hoverPoint.y; width: shot.width; height: 1
            color: Qt.rgba(1, 1, 1, 0.16)
        }
        Rectangle {
            visible: magnifier.at.x >= 0 && !magnifier.pinned
            x: magnifier.hoverPoint.x; y: 0; width: 1; height: shot.height
            color: Qt.rgba(1, 1, 1, 0.16)
        }
        // the moment the screen froze: a shutter's flash
        Rectangle {
            id: shutter
            anchors.fill: shot
            color: "white"; opacity: 0
            function flash() { if (studio.effects) flashing.restart() }
            NumberAnimation { id: flashing; target: shutter; property: "opacity"; from: 0.35; to: 0; duration: 320; easing.type: Easing.OutQuad }
        }
        // a saved target: its box pulses green and fades
        Rectangle {
            id: savedPulse
            property var box: [0, 0, 0, 0]
            function show(saved) { if (!saved || !studio.effects) return; box = saved; pulsing.restart() }
            visible: pulsing.running
            x: box[0] * shotWindow.scale; y: box[1] * shotWindow.scale
            width: box[2] * shotWindow.scale; height: box[3] * shotWindow.scale
            color: Qt.rgba(studio.colors.ok.r, studio.colors.ok.g, studio.colors.ok.b, 0.18)
            border.color: studio.colors.ok; border.width: 3; radius: 4
            transformOrigin: Item.Center
            ParallelAnimation {
                id: pulsing
                NumberAnimation { target: savedPulse; property: "scale"; from: 1; to: 1.18; duration: 480; easing.type: Easing.OutCubic }
                NumberAnimation { target: savedPulse; property: "opacity"; from: 1; to: 0; duration: 480; easing.type: Easing.InQuad }
            }
        }

        // C held: the saved image over the new one
        Image {
            visible: shotWindow.comparing && !!shotWindow.image && !!shotWindow.saved.picture
            source: shotWindow.saved.picture || ""
            x: imageBox.x; y: imageBox.y
            width: sourceSize.width * shotWindow.scale; height: sourceSize.height * shotWindow.scale
            opacity: 0.7; smooth: false
        }

        // the location: a crosshair, dragged to move it
        Item {
            id: locationMark
            visible: !!shotWindow.location
            opacity: shotWindow.tool === "location" ? 1 : 0.7
            x: (shotWindow.location ? shotWindow.location[0] : 0) * shotWindow.scale
            y: (shotWindow.location ? shotWindow.location[1] : 0) * shotWindow.scale
            Rectangle { x: -1; y: -12; width: 2; height: 24; color: shotWindow.locationInk }
            Rectangle { x: -12; y: -1; width: 24; height: 2; color: shotWindow.locationInk }
            Rectangle { x: -7; y: -7; width: 14; height: 14; radius: 7; color: "transparent"; border.color: shotWindow.locationInk; border.width: shotWindow.tool === "location" ? 3 : 2 }
            MouseArea {
                x: -12; y: -12; width: 24; height: 24
                enabled: shotWindow.tool === "location"
                cursorShape: Qt.SizeAllCursor
                onPressed: shotWindow.remember()
                onPositionChanged: function (mouse) {
                    if (!pressed) return
                    var at = mapToItem(shot, mouse.x, mouse.y)
                    shotWindow.location = shotWindow.toShot(at.x, at.y)
                }
            }
        }

        // readouts: click one to type exact numbers
        component Readout: Rectangle {
            id: readout
            property string text: ""
            property string value: ""   // the numbers to edit, "x, y, w, h"
            property color ink: studio.colors.text
            property bool editing: false
            signal edited(var numbers)
            height: 24; radius: 12
            width: editing ? 190 : label.implicitWidth + 18
            color: shotWindow.solid; border.color: studio.colors.line
            Text { id: label; visible: !readout.editing; anchors.centerIn: parent; text: readout.text; color: readout.ink; font.family: "monospace"; font.pixelSize: 11 }
            MouseArea { anchors.fill: parent; enabled: !readout.editing; cursorShape: Qt.IBeamCursor; onClicked: { readout.editing = true; field.text = readout.value; field.selectAll(); field.forceActiveFocus() } }
            Field {
                id: field
                visible: readout.editing
                anchors.fill: parent; leftPadding: 10
                ink: readout.ink; color: readout.ink; font.family: "monospace"; font.pixelSize: 11
                onAccepted: {
                    var numbers = text.split(/[\s,×x]+/).filter(function (part) { return part !== "" }).map(Number)
                    if (numbers.every(function (n) { return !isNaN(n) })) readout.edited(numbers)
                    readout.editing = false; stage.forceActiveFocus()
                }
                Keys.onEscapePressed: { readout.editing = false; stage.forceActiveFocus() }
                onActiveFocusChanged: if (!activeFocus) readout.editing = false
            }
        }
        Readout {
            visible: !!shotWindow.image
            x: imageBox.x + imageBox.width + 10; y: imageBox.y
            ink: shotWindow.imageInk
            text: shotWindow.image ? "image " + shotWindow.image[2] + " × " + shotWindow.image[3] : ""
            value: shotWindow.image ? shotWindow.image.join(", ") : ""
            onEdited: function (numbers) { if (numbers.length === 4) shotWindow.setPart("image", shotWindow.clamp(numbers)) }
        }
        Readout {
            visible: !!shotWindow.location
            x: locationMark.x + 18; y: locationMark.y + (shotWindow.image ? 10 : -12)
            ink: shotWindow.locationInk
            readonly property var centre: shotWindow.image ? [shotWindow.image[0] + shotWindow.image[2] / 2, shotWindow.image[1] + shotWindow.image[3] / 2] : null
            readonly property var offset: centre && shotWindow.location ? [Math.round(shotWindow.location[0] - centre[0]), Math.round(shotWindow.location[1] - centre[1])] : null
            text: !shotWindow.location ? "" : offset ? "location " + (offset[0] >= 0 ? "+" : "") + offset[0] + ", " + (offset[1] >= 0 ? "+" : "") + offset[1] + " from its centre" : "location " + shotWindow.location[0] + ", " + shotWindow.location[1]
            value: !shotWindow.location ? "" : offset ? offset.join(", ") : shotWindow.location.join(", ")
            onEdited: function (numbers) {
                if (numbers.length !== 2) return
                shotWindow.setPart("location", centre ? [centre[0] + numbers[0], centre[1] + numbers[1]] : numbers)
            }
        }
        Readout {
            visible: !!shotWindow.region
            x: (shotWindow.region ? shotWindow.region[0] : 0) * shotWindow.scale
            y: (shotWindow.region ? shotWindow.region[1] + shotWindow.region[3] : 0) * shotWindow.scale + 8
            readonly property bool holds: !!shotWindow.region && !!shotWindow.image && shotWindow.inside(shotWindow.region, shotWindow.image)
            ink: shotWindow.image && !holds ? studio.colors.warn : shotWindow.regionInk
            text: !shotWindow.region ? "" : "region " + (shotWindow.regionName ? shotWindow.regionName + " (shared) · " : "")
                + shotWindow.region.join(", ").replace(/, (\d+), (\d+)$/, " · $1 × $2")
                + (shotWindow.image ? (holds ? " · image inside ✓" : " · image outside ⚠") : "")
            value: shotWindow.region ? shotWindow.region.join(", ") : ""
            onEdited: function (numbers) { if (numbers.length === 4) shotWindow.setPart("region", shotWindow.clamp(numbers)) }
        }

        // the active target's name, by its box: to the right, or to the left near the screen's edge, under the image's
        // readout. Enter saves; Esc goes back to the shot
        Rectangle {
            id: naming
            objectName: "naming"
            readonly property var b: shotWindow.mainBox(shotWindow.live())
            readonly property real boxLeft: b ? b[0] * shotWindow.scale : 0
            readonly property real boxRight: b ? (b[0] + b[2]) * shotWindow.scale : 0
            readonly property real boxTop: b ? b[1] * shotWindow.scale : 0
            readonly property real boxMiddle: b ? (b[1] + b[3] / 2) * shotWindow.scale : 0
            readonly property bool flipped: boxRight + 12 + width > stage.width - 8
            visible: !!b
            x: flipped ? Math.max(8, boxLeft - 12 - width) : boxRight + 12
            y: Math.max(8, Math.min(stage.height - height - 8, flipped ? boxMiddle - height / 2 : Math.max(boxTop + 32, boxMiddle - height / 2)))
            width: 290; height: 40; radius: 20
            color: shotWindow.solid
            border.color: nameField.activeFocus ? shotWindow.inkOf(shotWindow.kind) : studio.colors.line
            Chip {
                id: namingKind
                x: 8; anchors.verticalCenter: parent.verticalCenter
                height: 24
                tone: "plain"
                text: shotWindow.kind ? shotWindow.kind.charAt(0).toUpperCase() + shotWindow.kind.slice(1) : ""
            }
            Field {
                id: nameField
                objectName: "nameField"
                quiet: true
                x: namingKind.x + namingKind.width + 4; width: parent.width - x - 8
                anchors.verticalCenter: parent.verticalCenter
                placeholderText: "Name, e.g. Menu.Start"
                font.family: "monospace"; font.pixelSize: 13
                ink: shotWindow.inkOf(shotWindow.kind)
                onAccepted: shotWindow.save()
                onTextEdited: shotWindow.showPill()
                // the name of a target there already: its region and location come back (only where none is made yet)
                onEditingFinished: shotWindow.takeSaved(text.trim())
                Keys.onEscapePressed: stage.forceActiveFocus()
            }
        }

        // Test's scan: a line sweeps the searched region, then the matches show
        Item {
            id: scan
            visible: sweeping.running
            property var area: [0, 0, 0, 0]
            x: area[0] * shotWindow.scale; y: area[1] * shotWindow.scale
            width: area[2] * shotWindow.scale; height: area[3] * shotWindow.scale
            property real done: 0
            function sweep(searched) { area = searched; done = 0; sweeping.restart() }
            Rectangle {  // the part already searched, faintly lit
                width: scan.width * scan.done; height: scan.height
                color: Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.08)
            }
            Rectangle {  // the line, with a soft trail
                x: scan.width * scan.done - width; width: 90; height: scan.height
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: "transparent" }
                    GradientStop { position: 0.92; color: Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.35) }
                    GradientStop { position: 1; color: studio.colors.accent }
                }
            }
            NumberAnimation {
                id: sweeping
                target: scan; property: "done"; from: 0; to: 1; duration: 520; easing.type: Easing.InOutQuad
                onFinished: shotWindow.showFound()
            }
        }

        // Test's matches, best first, each popping in after the one before
        Repeater {
            model: shotWindow.matches
            delegate: Rectangle {
                required property var modelData
                required property int index
                x: modelData.x * shotWindow.scale; y: modelData.y * shotWindow.scale
                width: modelData.w * shotWindow.scale; height: modelData.h * shotWindow.scale
                color: "transparent"; border.width: 2
                opacity: modelData.score >= shotWindow.similarity ? 1 : 0.3
                Behavior on opacity { NumberAnimation { duration: studio.effects ? 160 : 0 } }
                border.color: modelData.score >= shotWindow.similarity ? studio.colors.ok : studio.colors.warn
                transformOrigin: Item.Center
                SequentialAnimation on scale {
                    running: studio.effects
                    PauseAnimation { duration: index * 60 }
                    NumberAnimation { from: 1.4; to: 1; duration: 220; easing.type: Easing.OutBack }
                }
                Chip {
                    anchors { left: parent.left; bottom: parent.top; bottomMargin: 4 }
                    height: 20
                    tone: modelData.score >= shotWindow.similarity ? "ok" : "warn"
                    text: (index + 1) + " · " + modelData.score.toFixed(2)
                }
            }
        }

        // the guide's next image, top right (top left with the pill on the right edge), under the pill when that's
        // in its way; it slides away with the pill
        Rectangle {
            visible: shotWindow.current !== null
            x: pillZone.side === "right" ? 24 : parent.width - width - 24
            readonly property bool underPill: pillZone.side === "top" && pillZone.shownX + pillZone.width > x && pillZone.shownX < x + width
            y: shotWindow.tucked ? -height - 10 : underPill ? pillZone.shownY + pillZone.height + 12 : 24
            Behavior on y { NumberAnimation { duration: studio.effects ? 200 : 0; easing.type: Easing.OutCubic } }
            width: 380; height: guide.implicitHeight + 32; radius: 16
            color: shotWindow.solid; border.color: studio.colors.line
            Column {
                id: guide
                x: 18; y: 16; width: parent.width - 36; spacing: 8
                RowLayout {
                    width: parent.width
                    Text { text: shotWindow.current ? (shotWindow.current.screen || "Next to take") : ""; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold; Layout.fillWidth: true }
                    Text { text: capture.items.length + " left"; color: studio.colors.muted; font.pixelSize: 13 }
                }
                Row {
                    spacing: 8
                    Chip { text: shotWindow.current ? shotWindow.kindOf(shotWindow.current.kind) : ""; tone: "accent" }
                    Text { text: shotWindow.current ? shotWindow.current.name : ""; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; anchors.verticalCenter: parent.verticalCenter }
                }
                Text {  // a retake on a saved shot says so, and that a JPEG one is a little softer
                    objectName: "shotNote"
                    visible: text !== ""
                    text: capture.shotNote
                    color: studio.colors.warn; font.pixelSize: 12
                    width: parent.width; wrapMode: Text.Wrap
                }
                Text {
                    visible: text !== ""
                    text: shotWindow.current ? (shotWindow.current.say || "") : ""
                    color: studio.colors.slotBot; font.pixelSize: 13
                    width: parent.width; wrapMode: Text.Wrap
                }
            }
        }

        // the magnifier: the shot's own pixels, each `zoom` points wide (Ctrl+wheel: 2 to 24), with the target's parts
        // on them and the pixel under the mouse framed; Z pins it where it is. It flips near the edges.
        Item {
            id: magnifier
            objectName: "magnifier"
            readonly property int size: 150
            property real zoom: 8
            property bool pinned: false
            property point at: Qt.point(-1, -1)  // in the shot's pixels
            property point hoverPoint: Qt.point(0, 0)
            visible: at.x >= 0 && !(hoverPoint.y < pillZone.y + pillZone.height + 10 && hoverPoint.x > pillZone.x - 20 && hoverPoint.x < pillZone.x + pillZone.width + 20)
            x: hoverPoint.x + 24 + size > stage.width ? hoverPoint.x - size - 24 : hoverPoint.x + 24
            y: hoverPoint.y + 24 + size + 26 > stage.height ? hoverPoint.y - size - 50 : hoverPoint.y + 24
            width: size; height: size + 26
            // where a shot pixel lands in the magnifier
            function px(value, axis) { return magnifier.size / 2 + (value - (axis === 0 ? at.x : at.y) - 0.5) * zoom }
            Rectangle {
                width: magnifier.size; height: magnifier.size; radius: 14
                color: "black"; border.color: magnifier.pinned ? studio.colors.warn : studio.colors.accent; border.width: 2
                clip: true
                Image {  // the shot itself, not smoothed: each of its pixels a square of its own colour
                    source: capture.source
                    cache: false
                    smooth: false; mipmap: false
                    width: capture.shotWidth * magnifier.zoom; height: capture.shotHeight * magnifier.zoom
                    x: magnifier.px(0, 0); y: magnifier.px(0, 1)
                }
                Repeater {
                    model: [{ box: shotWindow.region, ink: shotWindow.regionInk }, { box: shotWindow.image, ink: shotWindow.imageInk }]
                    delegate: Rectangle {
                        required property var modelData
                        visible: !!modelData.box
                        x: modelData.box ? magnifier.px(modelData.box[0], 0) : 0; y: modelData.box ? magnifier.px(modelData.box[1], 1) : 0
                        width: modelData.box ? modelData.box[2] * magnifier.zoom : 0; height: modelData.box ? modelData.box[3] * magnifier.zoom : 0
                        color: "transparent"; border.color: modelData.ink; border.width: 2
                    }
                }
                Rectangle {
                    visible: !!shotWindow.location
                    x: shotWindow.location ? magnifier.px(shotWindow.location[0], 0) : 0; y: shotWindow.location ? magnifier.px(shotWindow.location[1], 1) : 0
                    width: magnifier.zoom; height: magnifier.zoom
                    color: "transparent"; border.color: shotWindow.locationInk; border.width: 2
                }
                Rectangle {  // the pixel under the mouse
                    anchors.centerIn: parent
                    width: magnifier.zoom + 2; height: width
                    color: "transparent"; border.color: "white"; border.width: 1
                }
            }
            Rectangle {
                y: magnifier.size + 4
                width: magnifier.size; height: 22; radius: 11
                color: shotWindow.solid
                Row {
                    anchors.centerIn: parent; spacing: 6
                    Text { text: magnifier.at.x + ", " + magnifier.at.y + " " + magnifier.zoom + "×"; color: studio.colors.text; font.family: "monospace"; font.pixelSize: 11 }
                    Rectangle { width: 10; height: 10; radius: 2; color: swatch.text || "transparent"; anchors.verticalCenter: parent.verticalCenter }
                    Text { id: swatch; text: magnifier.at.x >= 0 ? capture.colour(magnifier.at.x, magnifier.at.y) : ""; color: studio.colors.muted; font.family: "monospace"; font.pixelSize: 11 }
                }
            }
        }
        HoverHandler {
            target: stage
            onPointChanged: stage.follow(point.position)
        }
        WheelHandler {
            target: null
            acceptedModifiers: Qt.ControlModifier
            onWheel: function (event) {
                var steps = [2, 3, 4, 6, 8, 12, 16, 24]
                var at = steps.indexOf(magnifier.zoom)
                magnifier.zoom = steps[Math.max(0, Math.min(steps.length - 1, (at < 0 ? 4 : at) + (event.angleDelta.y > 0 ? 1 : -1)))]
            }
        }

        // ---- the pill (the shared one, on an edge or floating): the name, the kind being made, undo and redo, Test,
        // Save; by it, a message for a few seconds. While it's dragged the guide shows where it can go.
        PillGuide { anchors.fill: parent; place: capturePlace }
        PillBody {
            id: pillZone
            place: capturePlace
            cardWidth: 300
            property point held: Qt.point(0, 0)
            property real grabX: 0.5
            property real grabY: 0.5
            readonly property var spot: { capturePlace.screen; capturePlace.edge; return capturePlace.spotFor(face.width, face.height) }
            readonly property real shownX: spot.x - faceX
            readonly property real shownY: spot.y - faceY
            x: capturePlace.dragging ? held.x - faceX - grabX * face.width
                : shotWindow.tucked && side === "left" ? -width - 20
                : shotWindow.tucked && side === "right" ? stage.width + 20
                : shownX
            y: capturePlace.dragging ? held.y - faceY - grabY * face.height
                : shotWindow.tucked && side === "top" ? -height - 20
                : shotWindow.tucked && side === "bottom" ? stage.height + 20
                : shownY
            Behavior on x { enabled: !capturePlace.dragging; NumberAnimation { duration: studio.effects ? 200 : 0; easing.type: Easing.OutCubic } }
            Behavior on y { enabled: !capturePlace.dragging; NumberAnimation { duration: studio.effects ? 200 : 0; easing.type: Easing.OutCubic } }
            onShownXChanged: report()
            onShownYChanged: report()
            onWidthChanged: report()
            onHeightChanged: report()
            onFormChanged: capturePlace.setSize(form, face.width, face.height)
            // where it shows, stretched to its edge, for its hiding to watch the mouse around
            function report() {
                var left = shownX, top = shownY, right = shownX + width, bottom = shownY + height
                if (side === "top") top = 0
                else if (side === "bottom") bottom = stage.height
                else if (side === "left") left = 0
                else if (side === "right") right = stage.width
                captureHiding.setPlace(Math.round(left), Math.round(top), Math.round(right - left), Math.round(bottom - top), side)
            }
            Connections {
                target: stage
                function onWidthChanged() { capturePlace.useArea(0, 0, stage.width, stage.height) }
                function onHeightChanged() { capturePlace.useArea(0, 0, stage.width, stage.height) }
            }
            Component.onCompleted: capturePlace.useArea(0, 0, stage.width, stage.height)
            Connections {
                target: capturePlace
                function onChanged() { captureHiding.hold(capturePlace.floating || capturePlace.dragging); pillZone.report() }
            }
            onPressed: shotWindow.showPill()
            onGrabbed: function (gx, gy) {
                var at = face.mapFromGlobal(gx, gy)
                grabX = Math.max(0, Math.min(1, at.x / face.width))
                grabY = Math.max(0, Math.min(1, at.y / face.height))
                held = stage.mapFromGlobal(gx, gy)
                capturePlace.setSize(form, face.width, face.height)
                capturePlace.begin(held.x, held.y)
            }
            onMoved: function (gx, gy) { held = stage.mapFromGlobal(gx, gy); capturePlace.move(held.x, held.y) }
            onDropped: capturePlace.end()

            heading: [
                Text { text: "Capture"; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold },
                Item { Layout.fillWidth: true }
            ]

                // the kind being made: a ✓ on each the target has
                Segmented {
                    itemHeight: 32
                    vertical: shotWindow.stacked; columnWidth: 182
                    current: shotWindow.tool
                    model: [
                        { key: "image", label: "Image", icon: "▣", count: shotWindow.image ? "✓" : undefined },
                        { key: "region", label: "Region", icon: "⬚", count: shotWindow.region ? "✓" : undefined },
                        { key: "location", label: "Location", icon: "✛", count: shotWindow.location ? "✓" : undefined }
                    ]
                    onPicked: function (key) { shotWindow.choose(key) }
                }
                // where the image is searched: the whole screen, a shared region, or its own
                Segmented {
                    visible: shotWindow.tool === "region" && !!shotWindow.image
                    itemHeight: 32; strong: false
                    vertical: shotWindow.stacked; columnWidth: 182
                    current: shotWindow.searchIn
                    model: [
                        { key: "screen", label: "Whole screen" },
                        { key: "shared", label: "Shared ▾" },
                        { key: "own", label: "Its own" }
                    ]
                    onPicked: function (key) { shotWindow.searchOn(key); stage.forceActiveFocus() }
                }
                PillAction {
                    visible: !shotWindow.compact
                    labelled: shotWindow.stacked
                    glyph: "⌫"; label: "Remove"; tip: "Remove the " + shotWindow.tool + " (Delete)"
                    enabled: !!shotWindow.partOf(shotWindow.tool)
                    onClicked: { shotWindow.drop(shotWindow.tool); stage.forceActiveFocus() }
                }
                Rectangle {
                    visible: !shotWindow.compact
                    Layout.preferredWidth: shotWindow.stacked ? 182 : 1; Layout.preferredHeight: shotWindow.stacked ? 1 : 24
                    color: studio.colors.line
                }
                // the targets on this shot: a stack that opens into their tiles (under the row on the top and bottom
                // edges, here in the column on the sides and floating), and stepping through them
                StackToggle { visible: capture.several; Layout.fillWidth: shotWindow.stacked }
                ShotTargets {
                    objectName: "tilesColumn"
                    visible: shotWindow.compact && shotWindow.listOpen && shotWindow.shown.length > 0
                    vertical: true
                    Layout.preferredWidth: 182; Layout.preferredHeight: implicitHeight
                    model: shotWindow.shown
                    active: shotWindow.active
                    source: capture.source
                    onPicked: function (index) { shotWindow.activate(index); stage.forceActiveFocus() }
                    onRemoved: function (index) { shotWindow.removeTarget(index); stage.forceActiveFocus() }
                }
                PillAction { visible: capture.several && !shotWindow.stacked; glyph: "‹"; tip: "The previous target (Shift+N)"; enabled: shotWindow.shown.length > 0; onClicked: shotWindow.step(-1) }
                KeyCap { visible: capture.several && !shotWindow.stacked; text: "N" }
                PillAction { visible: capture.several && !shotWindow.stacked; glyph: "›"; tip: "The next target (N)"; enabled: shotWindow.shown.length > 0; onClicked: shotWindow.step(1) }
                PillAction { visible: capture.several && !shotWindow.stacked; glyph: "＋"; tip: "A new target on this shot (A)"; onClicked: shotWindow.addTarget() }
                Rectangle {
                    visible: capture.several
                    Layout.preferredWidth: shotWindow.stacked ? 182 : 1; Layout.preferredHeight: shotWindow.stacked ? 1 : 24
                    color: studio.colors.line
                }
                // several targets in a column: the small actions in two rows of glyphs, so the tiles get the room
                RowLayout {
                    visible: shotWindow.compact
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 6
                    PillAction { glyph: "⌫"; tip: "Remove the " + shotWindow.tool + " (Delete)"; enabled: !!shotWindow.partOf(shotWindow.tool); onClicked: { shotWindow.drop(shotWindow.tool); stage.forceActiveFocus() } }
                    PillAction { glyph: "＋"; tip: "A new target on this shot (A)"; onClicked: shotWindow.addTarget() }
                    PillAction { glyph: "↶"; tip: "Undo (Ctrl+Z)"; enabled: shotWindow.past.length > 0; onClicked: shotWindow.undo() }
                    PillAction { glyph: "↷"; tip: "Redo (Ctrl+Y)"; enabled: shotWindow.future.length > 0; onClicked: shotWindow.redo() }
                }
                RowLayout {
                    visible: shotWindow.compact
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 6
                    PillAction { glyph: "‹"; tip: "The previous target (Shift+N)"; enabled: shotWindow.shown.length > 0; onClicked: shotWindow.step(-1) }
                    KeyCap { text: "N" }
                    PillAction { glyph: "›"; tip: "The next target (N)"; enabled: shotWindow.shown.length > 0; onClicked: shotWindow.step(1) }
                    PillAction { glyph: "✕"; tip: "Close (Esc)"; onClicked: capture.close() }
                }
                PillAction { visible: !shotWindow.compact; labelled: shotWindow.stacked; glyph: "↶"; label: "Undo"; tip: "Undo (Ctrl+Z)"; enabled: shotWindow.past.length > 0; onClicked: shotWindow.undo() }
                PillAction { visible: !shotWindow.compact; labelled: shotWindow.stacked; glyph: "↷"; label: "Redo"; tip: "Redo (Ctrl+Y)"; enabled: shotWindow.future.length > 0; onClicked: shotWindow.redo() }
                Rectangle {
                    visible: !shotWindow.compact
                    Layout.preferredWidth: shotWindow.stacked ? 182 : 1; Layout.preferredHeight: shotWindow.stacked ? 1 : 24
                    color: studio.colors.line
                }
                PillButton {
                    small: true; icon: "⌕"
                    text: capture.several ? "Test all" : "Test"
                    Layout.fillWidth: shotWindow.stacked
                    enabled: capture.several ? shotWindow.shown.some(function (entry) { return !!entry.image }) : !!shotWindow.image
                    onClicked: shotWindow.test()
                }
                PillAction { visible: !shotWindow.compact; labelled: shotWindow.stacked; glyph: "✕"; label: "Close"; tip: "Close (Esc)"; onClicked: capture.close() }
                PillButton {
                    objectName: "saveButton"
                    kind: "primary"; small: true
                    text: capture.several && shotWindow.shown.length > 1 ? "Save " + shotWindow.shown.length : "Save"
                    Layout.fillWidth: shotWindow.stacked
                    onClicked: shotWindow.save()
                }

            drawer: ShotTargets {
                objectName: "tilesRow"
                visible: capture.several && !shotWindow.stacked && shotWindow.listOpen && shotWindow.shown.length > 0
                width: parent ? parent.width : 0; height: implicitHeight
                model: shotWindow.shown
                active: shotWindow.active
                source: capture.source
                onPicked: function (index) { shotWindow.activate(index); stage.forceActiveFocus() }
                onRemoved: function (index) { shotWindow.removeTarget(index); stage.forceActiveFocus() }
            }

            below: Column {
                id: under
                visible: shotWindow.note !== "" || shotWindow.matches.length > 0 || shotWindow.regionsOpen
                width: parent.width
                spacing: 8
                Rectangle {  // the bot's regions to search this image in
                    id: regionMenu
                    objectName: "regionMenu"
                    visible: shotWindow.regionsOpen
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 340; height: Math.min(360, choices.implicitHeight + 16); radius: 16
                    color: shotWindow.solid; border.color: studio.colors.line
                    onVisibleChanged: if (!visible) shotWindow.previewRegion = null
                    Flickable {
                        id: choicesView
                        anchors.fill: parent; anchors.margins: 8
                        contentHeight: choices.implicitHeight; clip: true
                        SmoothWheel { view: choicesView }
                        Column {
                            id: choices
                            spacing: 2
                            // the region drawn, shared under a name of its own
                            Row {
                                visible: !!shotWindow.region && !shotWindow.regionName
                                spacing: 6
                                Field {
                                    id: shareName
                                    ink: shotWindow.regionInk
                                    width: 220; height: 34
                                    placeholderText: "Share the drawn region as…"
                                    text: nameField.text.indexOf(".") > 0 ? nameField.text.split(".")[0] + ".Menu" : ""
                                    onAccepted: shotWindow.shareRegion(text)
                                }
                                PillButton { small: true; text: "Share"; onClicked: shotWindow.shareRegion(shareName.text) }
                            }
                            Text {
                                visible: shotWindow.regionChoices.length === 0 && !shotWindow.region
                                width: 324; wrapMode: Text.Wrap
                                text: "No regions yet. Draw one with Region picked, then share it here so other images can be searched in it."
                                color: studio.colors.muted; font.pixelSize: 12
                            }
                            Repeater {
                                model: shotWindow.regionChoices
                                delegate: MenuLine {
                                    required property var modelData
                                    width: 324
                                    icon: modelData.name ? "⬚" : "▣"
                                    iconColor: shotWindow.regionInk
                                    text: modelData.name || ("Like " + modelData.used_by[0] + (modelData.used_by.length > 1 ? " and " + (modelData.used_by.length - 1) + " more" : ""))
                                    detail: modelData.region[2] + " × " + modelData.region[3]
                                        + (modelData.name ? " · shared" + (modelData.used_by.length ? " by " + modelData.used_by.length : "") : " · copied, not shared")
                                    onHoveredChanged: shotWindow.previewRegion = hovered ? modelData.region : null
                                    onClicked: shotWindow.useRegion(modelData)
                                }
                            }
                        }
                    }
                }
                Rectangle {  // the last message
                    visible: shotWindow.note !== ""
                    anchors.horizontalCenter: parent.horizontalCenter
                    readonly property color ink: shotWindow.noteBad ? studio.colors.warn : studio.colors.ok
                    // one line where there's room; beside a column or a card it wraps
                    readonly property real widest: pillZone.besides || pillZone.floating ? 300 : 720
                    width: Math.min(noteText.implicitWidth, widest - 24) + 24; height: noteText.height + 14; radius: 15
                    color: shotWindow.solid; border.color: ink
                    Text {
                        id: noteText
                        anchors.centerIn: parent
                        width: Math.min(implicitWidth, parent.widest - 24)
                        wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter
                        text: shotWindow.note; color: parent.ink; font.pixelSize: 12; font.weight: Font.DemiBold
                    }
                }
                // after Test: the similarity a match needs; matches under it fade
                Rectangle {
                    visible: shotWindow.matches.length > 0
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 330; height: 44; radius: 22
                    color: shotWindow.solid; border.color: studio.colors.line
                    Row {
                        anchors.centerIn: parent; spacing: 12
                        Text { text: "needs"; color: studio.colors.muted; font.pixelSize: 13; anchors.verticalCenter: parent.verticalCenter }
                        ValueSlider {
                            low: 0.6; high: 1.0; decimals: 2; value: shotWindow.similarity
                            onEdited: function (value) { shotWindow.similarity = value }
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }
            }
        }
    }
}
