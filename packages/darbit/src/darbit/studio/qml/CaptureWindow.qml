// Capture: the frozen screen, full screen. A target is an image, the region it's searched in and the location to
// click, made together. The kind chosen in the pill (1, 2, 3 or Tab) is what a click or drag makes and what the handles
// and arrows change: click to box an image or region (again for bigger, right-click smaller) or drag one, click the
// location. The pill sits at the top and slides out of sight a few seconds after the mouse leaves it; the top edge
// brings it back. Ctrl+Z / Ctrl+Y undo and redo; T tests; Enter saves.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
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
    property string note: ""
    property bool noteBad: false
    property bool tucked: false          // the pill slid up out of sight
    property bool comparing: false       // C held: the saved image over the new one
    readonly property real scale: Math.min(width / Math.max(1, capture.shotWidth), height / Math.max(1, capture.shotHeight))
    readonly property var current: capture.items.length > 0 ? capture.items[0] : null
    readonly property string kind: image ? "image" : region ? "region" : location ? "location" : ""
    readonly property var box: image     // the image, by its old name
    readonly property var kinds: ["image", "region", "location"]
    readonly property color imageInk: studio.colors.accent
    readonly property color regionInk: studio.colors.accent2
    readonly property color locationInk: studio.colors.ok
    readonly property color solid: Qt.rgba(studio.colors.glassStrong.r, studio.colors.glassStrong.g, studio.colors.glassStrong.b, 1)

    onVisibleChanged: if (visible) { reset(); nameField.text = current ? current.name : ""; takeSaved(nameField.text); nameField.forceActiveFocus(); showPill() }
    onCurrentChanged: if (current && visible) { nameField.text = current.name; tool = kindOf(current.kind) }

    function kindOf(name) { return name === "region" ? "region" : name === "location" || name === "point" ? "location" : "image" }
    function inkOf(name) { return name === "region" ? regionInk : name === "location" ? locationInk : imageInk }

    // ---- the target and its history
    function snapshot() { return { image: image, region: region, location: location } }
    function restore(state) { image = state.image; region = state.region; location = state.location; matches = [] }
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
    function choose(name) { tool = name; stage.forceActiveFocus() }
    function reset() {
        image = null; region = null; location = null; past = []; future = []; saved = ({})
        boxes = []; matches = []; waiting = null; note = ""; lastClick = null
        tool = current ? kindOf(current.kind) : "image"
    }
    // a retake: the target's saved region and location come back, and its image is there to compare with
    function takeSaved(name) {
        saved = name ? capture.existing(name) : ({})
        if (saved.region && !region) region = saved.region
        if (saved.location && !location) location = saved.location
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
    function clicked(x, y, bigger) {
        var at = toShot(x, y)
        if (tool === "location") { setPart("location", at); return }
        var same = lastClick && Math.abs(lastClick[0] - at[0]) < 4 && Math.abs(lastClick[1] - at[1]) < 4
        if (!same) {
            var found = capture.candidates(at[0], at[1], tool)
            boxes = found.boxes; chosen = found.start || 0; lastClick = at
        } else if (boxes.length) {
            chosen = Math.max(0, Math.min(boxes.length - 1, chosen + (bigger ? 1 : -1)))
        }
        if (boxes.length) setPart(tool, boxes[chosen])
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
    function showFound() {
        var found = waiting
        waiting = null
        if (!found) return
        matches = found.matches || []
        var strong = matches.filter(function (match) { return match.score >= shotWindow.similarity }).length
        var others = matches.length - strong
        var where = strong === 0 ? "Not found" : strong === 1 ? "Found once" : "Found " + strong + " times"
        var alike = others === 0 ? "nothing else close" : others === 1 ? "1 look-alike under the line" : others + " look-alikes under the line"
        say(where + " at " + shotWindow.similarity.toFixed(2) + (region ? " in its region" : " on the whole screen") + " · " + alike + " · " + found.ms + " ms", strong !== 1)
    }
    function save() {
        var name = nameField.text.trim()
        if (!kind) { say("Make an image, a region or a location first", true); return }
        var result = capture.save(name, kind, image, region, location)
        if (result.error) { say(result.error, true); return }
        var told = result.message || ("Saved " + name), bad = !!result.risky
        reset()
        nameField.text = current ? current.name : ""
        takeSaved(nameField.text)
        say(told, bad)
    }

    // ---- the pill's hiding, and its messages fading
    function showPill() { tucked = false; tuckTimer.restart() }
    Timer { id: tuckTimer; interval: 3000; onTriggered: shotWindow.tucked = true }
    Timer { id: noteTimer; interval: 5000; onTriggered: shotWindow.note = "" }

    Item {
        id: stage
        anchors.fill: parent
        focus: true
        Keys.onPressed: function (event) {
            var step = (event.modifiers & Qt.ShiftModifier) ? 10 : 1
            var control = (event.modifiers & Qt.ControlModifier) !== 0
            if (event.key === Qt.Key_Escape) { if (shotWindow.partOf(shotWindow.tool)) shotWindow.drop(shotWindow.tool); else capture.close() }
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) shotWindow.save()
            else if (control && event.key === Qt.Key_Z && (event.modifiers & Qt.ShiftModifier)) shotWindow.redo()
            else if (control && event.key === Qt.Key_Z) shotWindow.undo()
            else if (control && event.key === Qt.Key_Y) shotWindow.redo()
            else if (event.key === Qt.Key_1) shotWindow.choose("image")
            else if (event.key === Qt.Key_2) shotWindow.choose("region")
            else if (event.key === Qt.Key_3) shotWindow.choose("location")
            else if (event.key === Qt.Key_Tab) shotWindow.choose(shotWindow.kinds[(shotWindow.kinds.indexOf(shotWindow.tool) + 1) % 3])
            else if (event.key === Qt.Key_T) shotWindow.test()
            else if (event.key === Qt.Key_Delete || event.key === Qt.Key_Backspace) shotWindow.drop(shotWindow.tool)
            else if (event.key === Qt.Key_Z) magnifier.pinned = !magnifier.pinned
            else if (event.key === Qt.Key_C && !event.isAutoRepeat) shotWindow.comparing = true
            else if (event.key === Qt.Key_Left) shotWindow.nudge(-step, 0, control)
            else if (event.key === Qt.Key_Right) shotWindow.nudge(step, 0, control)
            else if (event.key === Qt.Key_Up) shotWindow.nudge(0, -step, control)
            else if (event.key === Qt.Key_Down) shotWindow.nudge(0, step, control)
            else return
            event.accepted = true
        }
        Keys.onReleased: function (event) { if (event.key === Qt.Key_C && !event.isAutoRepeat) shotWindow.comparing = false }

        Image {
            id: shot
            source: capture.source
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
            property var from: null
            property bool dragged: false
            property var moving: null  // the chosen box and the shot pixel the drag started at
            onPressed: function (mouse) {
                from = [mouse.x, mouse.y]; dragged = false; moving = null; stage.forceActiveFocus()
                var part = shotWindow.tool !== "location" ? shotWindow.partOf(shotWindow.tool) : null
                var at = shotWindow.toShot(mouse.x, mouse.y)
                if (part && at[0] >= part[0] && at[0] <= part[0] + part[2] && at[1] >= part[1] && at[1] <= part[1] + part[3])
                    moving = { box: part.slice(), at: at }
            }
            onPositionChanged: function (mouse) {
                if (!from || mouse.buttons !== Qt.LeftButton) return
                if (!dragged && Math.abs(mouse.x - from[0]) + Math.abs(mouse.y - from[1]) < 6) return
                if (!dragged) shotWindow.remember()
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
                if (!dragged) shotWindow.clicked(mouse.x, mouse.y, mouse.button === Qt.LeftButton)
                from = null; moving = null
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
            color: "transparent"
            border.color: ink; border.width: chosen ? 2 : 1
            opacity: chosen ? 1 : 0.6
            Repeater {
                model: partBox.chosen ? 8 : 0
                delegate: Rectangle {
                    required property int index
                    readonly property real fx: [0, 0.5, 1, 1, 1, 0.5, 0, 0][index]
                    readonly property real fy: [0, 0, 0, 0.5, 1, 1, 1, 0.5][index]
                    x: partBox.width * fx - 5; y: partBox.height * fy - 5
                    width: 10; height: 10; radius: 2
                    color: "white"; border.color: partBox.ink
                    MouseArea {
                        anchors.fill: parent; anchors.margins: -4
                        cursorShape: (index % 4 === 1) ? Qt.SizeVerCursor : (index % 4 === 3) ? Qt.SizeHorCursor : (index === 0 || index === 4) ? Qt.SizeFDiagCursor : Qt.SizeBDiagCursor
                        onPressed: shotWindow.remember()
                        onPositionChanged: function (mouse) {
                            if (!pressed) return
                            var at = mapToItem(shot, mouse.x, mouse.y), p = shotWindow.toShot(at.x, at.y), b = partBox.b
                            var left = b[0], top = b[1], right = b[0] + b[2], bottom = b[1] + b[3]
                            if (fx === 0) left = Math.min(p[0], right - 1)
                            if (fx === 1) right = Math.max(p[0], left + 1)
                            if (fy === 0) top = Math.min(p[1], bottom - 1)
                            if (fy === 1) bottom = Math.max(p[1], top + 1)
                            var next = shotWindow.clamp([left, top, right - left, bottom - top])
                            if (partBox.part === "image") shotWindow.image = next; else shotWindow.region = next
                            shotWindow.matches = []
                        }
                    }
                }
            }
        }
        PartBox { part: "region"; value: shotWindow.region }
        PartBox { id: imageBox; part: "image"; value: shotWindow.image }

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
            TextField {
                id: field
                visible: readout.editing
                anchors.fill: parent; leftPadding: 10
                color: readout.ink; font.family: "monospace"; font.pixelSize: 11
                background: Rectangle { radius: 12; color: studio.colors.raised; border.color: readout.ink }
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
            text: !shotWindow.region ? "" : "region " + shotWindow.region.join(", ").replace(/, (\d+), (\d+)$/, " · $1 × $2")
                + (shotWindow.image ? (holds ? " · image inside ✓" : " · image outside ⚠") : "")
            value: shotWindow.region ? shotWindow.region.join(", ") : ""
            onEdited: function (numbers) { if (numbers.length === 4) shotWindow.setPart("region", shotWindow.clamp(numbers)) }
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

        // the guide's next image, top right; it slides away with the pill
        Rectangle {
            visible: shotWindow.current !== null
            anchors.right: parent.right; anchors.rightMargin: 24
            y: shotWindow.tucked ? -height - 10 : 24
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
            onPointChanged: {
                var p = point.position
                // the pill: the top edge brings it back; away from it, it slides out of sight after a few seconds
                var near = p.y <= pillZone.y + pillZone.height + 24 && p.x >= pillZone.x - 24 && p.x <= pillZone.x + pillZone.width + 24
                if (shotWindow.tucked) { if (p.y <= 2) shotWindow.showPill() }
                else if (near) tuckTimer.stop()
                else if (!tuckTimer.running) tuckTimer.start()
                if (magnifier.pinned) return
                magnifier.hoverPoint = p
                // the pixel the mouse is on, not the nearest corner
                magnifier.at = Qt.point(Math.min(capture.shotWidth - 1, Math.floor(p.x / shotWindow.scale)),
                                        Math.min(capture.shotHeight - 1, Math.floor(p.y / shotWindow.scale)))
            }
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

        // ---- the pill, top centre: the name, the kind being made, undo and redo, Test, Save; under it, a message
        // for a few seconds. It slides out of sight and comes back at the top edge.
        Item {
            id: pillZone
            width: pill.width
            height: pill.height + (under.visible ? 10 + under.height : 0)
            x: (stage.width - width) / 2
            y: shotWindow.tucked ? -height - 20 : 14
            Behavior on y { NumberAnimation { duration: studio.effects ? 200 : 0; easing.type: Easing.OutCubic } }
            HoverHandler { onHoveredChanged: if (hovered) tuckTimer.stop() }

            FloatingPill {
                id: pill
                TextField {
                    id: nameField
                    objectName: "nameField"
                    placeholderText: "Name, e.g. Lobby.Play"
                    placeholderTextColor: studio.colors.faint
                    Layout.preferredWidth: 210; Layout.preferredHeight: 40
                    leftPadding: 16
                    color: studio.colors.text
                    font.pixelSize: 14; font.weight: Font.DemiBold
                    onAccepted: shotWindow.save()
                    onTextEdited: shotWindow.showPill()
                    onEditingFinished: if (!shotWindow.image && !shotWindow.region && !shotWindow.location) shotWindow.takeSaved(text.trim())
                    Keys.onEscapePressed: capture.close()
                    background: Rectangle { radius: 20; color: studio.colors.raised; border.color: nameField.activeFocus ? studio.colors.accent : "transparent" }
                }
                // the kind being made: a ✓ on each the target has
                Segmented {
                    itemHeight: 32
                    current: shotWindow.tool
                    model: [
                        { key: "image", label: "Image", icon: "▣", count: shotWindow.image ? "✓" : undefined },
                        { key: "region", label: "Region", icon: "⬚", count: shotWindow.region ? "✓" : undefined },
                        { key: "location", label: "Location", icon: "✛", count: shotWindow.location ? "✓" : undefined }
                    ]
                    onPicked: function (key) { shotWindow.choose(key) }
                }
                IconButton {
                    glyph: "⌫"; tip: "Remove the " + shotWindow.tool + " (Delete)"
                    enabled: !!shotWindow.partOf(shotWindow.tool)
                    onClicked: { shotWindow.drop(shotWindow.tool); stage.forceActiveFocus() }
                }
                Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
                IconButton { glyph: "↶"; tip: "Undo (Ctrl+Z)"; enabled: shotWindow.past.length > 0; onClicked: shotWindow.undo() }
                IconButton { glyph: "↷"; tip: "Redo (Ctrl+Y)"; enabled: shotWindow.future.length > 0; onClicked: shotWindow.redo() }
                Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
                PillButton { small: true; icon: "⌕"; text: "Test"; enabled: !!shotWindow.image; onClicked: shotWindow.test() }
                IconButton { glyph: "✕"; tip: "Close (Esc)"; onClicked: capture.close() }
                PillButton { kind: "primary"; small: true; text: "Save"; onClicked: shotWindow.save() }
            }
            Column {
                id: under
                visible: shotWindow.note !== "" || shotWindow.matches.length > 0
                anchors { horizontalCenter: pill.horizontalCenter; top: pill.bottom; topMargin: 10 }
                spacing: 8
                Rectangle {  // the last message
                    visible: shotWindow.note !== ""
                    anchors.horizontalCenter: parent.horizontalCenter
                    readonly property color ink: shotWindow.noteBad ? studio.colors.warn : studio.colors.ok
                    width: noteText.implicitWidth + 24; height: 30; radius: 15
                    color: shotWindow.solid; border.color: ink
                    Text { id: noteText; anchors.centerIn: parent; text: shotWindow.note; color: parent.ink; font.pixelSize: 12; font.weight: Font.DemiBold }
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
                        Slider {
                            width: 180; from: 0.6; to: 1.0; value: shotWindow.similarity
                            onMoved: shotWindow.similarity = Math.round(value * 100) / 100
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text { text: shotWindow.similarity.toFixed(2); color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }
                    }
                }
            }
        }
    }
}
