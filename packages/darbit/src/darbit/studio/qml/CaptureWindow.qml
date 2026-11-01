// Capture (round 10, A): the frozen screen, full screen. One target is a picture, the area it's searched in and where
// to click it, made together with the mouse: drag or click for the picture (again for bigger, right-click smaller),
// Shift+drag for its area, Ctrl+click for the point. The pill at the top slides away a few seconds after the mouse
// leaves it; the top edge brings it back. Ctrl+Z / Ctrl+Y undo and redo every change; T tests; Enter saves.
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

    // the target, in the shot's pixels: [x, y, w, h] boxes and an [x, y] point, each null until made
    property var picture: null
    property var area: null
    property var point: null
    property string focusOn: "picture"   // the part arrows, handles, Tab and Delete work on
    property var past: []                // undo: the target as it was before each change
    property var future: []              // redo
    property double nudgedAt: 0          // a burst of arrow presses is one undo step
    property var saved: ({})             // what a retaken target already has: region, offset, location, picture
    property var boxes: []               // the candidates around the last click, smallest first
    property int chosen: 0
    property var lastClick: null
    property var matches: []
    property var waiting: null           // Test's answer while the scan sweeps the searched area
    property real similarity: 0.9        // after Test: matches under it fade
    property string note: ""
    property bool noteBad: false
    property bool tucked: false          // the pill slid up out of the way
    property bool comparing: false       // C held: the saved picture over the new one
    readonly property real scale: Math.min(width / Math.max(1, capture.shotWidth), height / Math.max(1, capture.shotHeight))
    readonly property var current: capture.items.length > 0 ? capture.items[0] : null
    readonly property string kind: picture ? "image" : area ? "region" : point ? "point" : ""
    readonly property var box: picture   // the picture, by its old name
    // what a plain drag or click makes: the picture, unless the guide asks for an area or a point
    readonly property string plainMakes: current && current.kind === "region" ? "area" : current && current.kind === "point" ? "point" : "picture"
    readonly property color pictureInk: studio.colors.accent
    readonly property color areaInk: studio.colors.accent2
    readonly property color pointInk: studio.colors.ok

    onVisibleChanged: if (visible) { reset(); nameField.text = current ? current.name : ""; takeSaved(nameField.text); nameField.forceActiveFocus(); showPill() }
    onCurrentChanged: if (current && visible) { nameField.text = current.name }

    // ---- the target and its history
    function snapshot() { return { picture: picture, area: area, point: point } }
    function restore(state) { picture = state.picture; area = state.area; point = state.point; matches = [] }
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
        if (part === "picture") {
            picture = value
            // a retake keeps where it clicked, from the new picture's centre
            if (value && !point && saved.offset) point = [value[0] + value[2] / 2 + saved.offset[0], value[1] + value[3] / 2 + saved.offset[1]]
        } else if (part === "area") area = value
        else point = value
        focusOn = part
        matches = []
    }
    function partOf(name) { return name === "picture" ? picture : name === "area" ? area : point }
    function drop(name) { if (partOf(name)) setPart(name, null) }
    function reset() {
        picture = null; area = null; point = null; past = []; future = []; saved = ({})
        boxes = []; matches = []; waiting = null; note = ""; lastClick = null; focusOn = plainMakes
    }
    // a retake: the target's saved area and point come back, and its picture is there to compare with
    function takeSaved(name) {
        saved = name ? capture.existing(name) : ({})
        if (saved.region && !area) area = saved.region
        if (saved.location && !point) point = saved.location
    }

    function toShot(x, y) { return [Math.round(x / scale), Math.round(y / scale)] }
    function clamp(next) {
        var x = Math.max(0, Math.min(next[0], capture.shotWidth - 1)), y = Math.max(0, Math.min(next[1], capture.shotHeight - 1))
        return [x, y, Math.max(1, Math.min(next[2], capture.shotWidth - x)), Math.max(1, Math.min(next[3], capture.shotHeight - y))]
    }
    function say(text, bad) { note = text; noteBad = !!bad; if (text) showPill() }
    function inside(outer, inner) { return outer[0] <= inner[0] && outer[1] <= inner[1] && outer[0] + outer[2] >= inner[0] + inner[2] && outer[1] + outer[3] >= inner[1] + inner[3] }

    // a click: the box around it, or the next bigger (left) or smaller (right) one on a click at the same spot
    function clicked(x, y, bigger) { pick(x, y, bigger, false) }
    function pick(x, y, bigger, asArea) {
        var at = toShot(x, y)
        var same = lastClick && Math.abs(lastClick[0] - at[0]) < 4 && Math.abs(lastClick[1] - at[1]) < 4
        if (!same) {
            var found = capture.candidates(at[0], at[1], asArea ? "region" : "image")
            boxes = found.boxes; chosen = found.start || 0; lastClick = at
        } else if (boxes.length) {
            chosen = Math.max(0, Math.min(boxes.length - 1, chosen + (bigger ? 1 : -1)))
        }
        if (boxes.length) setPart(asArea ? "area" : "picture", boxes[chosen])
    }
    function nudge(dx, dy, grow) {
        var part = partOf(focusOn)
        if (!part) return
        if (Date.now() - nudgedAt > 700) remember()
        nudgedAt = Date.now()
        if (focusOn === "point") point = [Math.max(0, Math.min(capture.shotWidth - 1, part[0] + dx)), Math.max(0, Math.min(capture.shotHeight - 1, part[1] + dy))]
        else {
            var next = clamp(grow ? [part[0], part[1], part[2] + dx, part[3] + dy] : [part[0] + dx, part[1] + dy, part[2], part[3]])
            if (focusOn === "picture") picture = next; else area = next
        }
        matches = []
    }
    function cycleFocus() {
        var order = ["picture", "area", "point"]
        focusOn = order[(order.indexOf(focusOn) + 1) % 3]
        say(partOf(focusOn) ? "Arrows move the " + focusOn : hintFor(focusOn), false)
    }
    function hintFor(part) {
        return part === "area" ? "Shift+drag the area it's searched in" : part === "point" ? "Ctrl+click where to click it" : "Drag or click the picture"
    }

    function test() {
        if (!picture) { say("Box a picture first", true); return }
        var found = capture.test(picture, area)
        if (found.error) { say(found.error, true); return }
        matches = []
        note = ""
        waiting = found
        if (studio.effects && found.searched) scan.sweep(found.searched)
        else showFound()
    }
    // what Test found: the picture itself counts once; look-alikes are the other places, scoring under the line
    function showFound() {
        var found = waiting
        waiting = null
        if (!found) return
        matches = found.matches || []
        var strong = matches.filter(function (match) { return match.score >= shotWindow.similarity }).length
        var others = matches.length - strong
        var where = strong === 0 ? "Not found" : strong === 1 ? "Found once" : "Found " + strong + " times"
        var alike = others === 0 ? "nothing else close" : others === 1 ? "1 look-alike under the line" : others + " look-alikes under the line"
        say(where + " at " + shotWindow.similarity.toFixed(2) + (area ? " in its area" : " on the whole screen") + " · " + alike + " · " + found.ms + " ms", strong !== 1)
    }
    function save() {
        var name = nameField.text.trim()
        if (!kind) { say("Make a picture, an area or a point first", true); return }
        var result = capture.save(name, kind, picture, area, point)
        if (result.error) { say(result.error, true); return }
        say(result.message || ("Saved " + name), !!result.risky)
        var keep = note, bad = noteBad
        reset()
        nameField.text = current ? current.name : ""
        takeSaved(nameField.text)
        say(keep, bad)
    }

    // ---- the pill's hiding
    function showPill() { tucked = false; tuckTimer.restart() }
    Timer { id: tuckTimer; interval: 3000; onTriggered: shotWindow.tucked = true }

    Item {
        id: stage
        anchors.fill: parent
        focus: true
        Keys.onPressed: function (event) {
            var step = (event.modifiers & Qt.ShiftModifier) ? 10 : 1
            var grow = (event.modifiers & Qt.ControlModifier) !== 0
            var control = (event.modifiers & Qt.ControlModifier) !== 0
            if (event.key === Qt.Key_Escape) { if (shotWindow.partOf(shotWindow.focusOn)) shotWindow.drop(shotWindow.focusOn); else capture.close() }
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) shotWindow.save()
            else if (control && event.key === Qt.Key_Z && (event.modifiers & Qt.ShiftModifier)) shotWindow.redo()
            else if (control && event.key === Qt.Key_Z) shotWindow.undo()
            else if (control && event.key === Qt.Key_Y) shotWindow.redo()
            else if (event.key === Qt.Key_T) shotWindow.test()
            else if (event.key === Qt.Key_Tab) shotWindow.cycleFocus()
            else if (event.key === Qt.Key_Delete || event.key === Qt.Key_Backspace) shotWindow.drop(shotWindow.focusOn)
            else if (event.key === Qt.Key_Z) magnifier.pinned = !magnifier.pinned
            else if (event.key === Qt.Key_C && !event.isAutoRepeat) shotWindow.comparing = true
            else if (event.key === Qt.Key_Left) shotWindow.nudge(-step, 0, grow)
            else if (event.key === Qt.Key_Right) shotWindow.nudge(step, 0, grow)
            else if (event.key === Qt.Key_Up) shotWindow.nudge(0, -step, grow)
            else if (event.key === Qt.Key_Down) shotWindow.nudge(0, step, grow)
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

        // the shot outside the picture, dimmed (the design system's screen-dim)
        Item {
            id: dim
            visible: !!shotWindow.picture
            readonly property var b: shotWindow.picture ? shotWindow.picture.map(function (v) { return Math.round(v * shotWindow.scale) }) : [0, 0, 0, 0]
            anchors.fill: shot
            Rectangle { color: Qt.rgba(0, 0, 0, 0.5); x: 0; y: 0; width: dim.width; height: dim.b[1] }
            Rectangle { color: Qt.rgba(0, 0, 0, 0.5); x: 0; y: dim.b[1] + dim.b[3]; width: dim.width; height: dim.height - y }
            Rectangle { color: Qt.rgba(0, 0, 0, 0.5); x: 0; y: dim.b[1]; width: dim.b[0]; height: dim.b[3] }
            Rectangle { color: Qt.rgba(0, 0, 0, 0.5); x: dim.b[0] + dim.b[2]; y: dim.b[1]; width: dim.width - x; height: dim.b[3] }
        }

        // drag: the picture (Shift: the area); click: the box around it (Ctrl: the point). Dragging inside the part
        // being worked on moves it.
        MouseArea {
            id: drawing
            anchors.fill: shot
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            property var from: null
            property bool dragged: false
            property string making: "picture"
            property var moving: null  // the part's box and the shot pixel the drag started at
            onPressed: function (mouse) {
                from = [mouse.x, mouse.y]; dragged = false; moving = null; stage.forceActiveFocus()
                making = (mouse.modifiers & Qt.ShiftModifier) ? "area" : (mouse.modifiers & Qt.ControlModifier) ? "point" : shotWindow.plainMakes
                var part = shotWindow.focusOn !== "point" ? shotWindow.partOf(shotWindow.focusOn) : null
                var at = shotWindow.toShot(mouse.x, mouse.y)
                if (!(mouse.modifiers & (Qt.ShiftModifier | Qt.ControlModifier)) && part
                        && at[0] >= part[0] && at[0] <= part[0] + part[2] && at[1] >= part[1] && at[1] <= part[1] + part[3])
                    moving = { box: part.slice(), at: at }
            }
            onPositionChanged: function (mouse) {
                if (!from || mouse.buttons !== Qt.LeftButton) return
                if (!dragged && Math.abs(mouse.x - from[0]) + Math.abs(mouse.y - from[1]) < 6) return
                if (!dragged) shotWindow.remember()
                dragged = true
                shotWindow.matches = []
                var at = shotWindow.toShot(mouse.x, mouse.y)
                if (moving) {
                    var moved = shotWindow.clamp([moving.box[0] + at[0] - moving.at[0], moving.box[1] + at[1] - moving.at[1], moving.box[2], moving.box[3]])
                    if (shotWindow.focusOn === "picture") shotWindow.picture = moved; else shotWindow.area = moved
                    return
                }
                if (making === "point") { shotWindow.point = at; shotWindow.focusOn = "point"; return }
                var a = shotWindow.toShot(Math.min(from[0], mouse.x), Math.min(from[1], mouse.y))
                var b = shotWindow.toShot(Math.max(from[0], mouse.x), Math.max(from[1], mouse.y))
                var drawn = shotWindow.clamp([a[0], a[1], b[0] - a[0], b[1] - a[1]])
                if (making === "area") shotWindow.area = drawn; else shotWindow.picture = drawn
                shotWindow.focusOn = making
                shotWindow.boxes = []; shotWindow.lastClick = null
            }
            onReleased: function (mouse) {
                if (!dragged) {
                    if (making === "point") shotWindow.setPart("point", shotWindow.toShot(mouse.x, mouse.y))
                    else shotWindow.pick(mouse.x, mouse.y, mouse.button === Qt.LeftButton, making === "area")
                }
                from = null; moving = null
            }
        }

        // a box (the picture or its area) with its handles while it's the part being worked on
        component PartBox: Rectangle {
            id: partBox
            property string part: "picture"
            property var value: null
            property color ink: "white"
            readonly property var b: value || [0, 0, 0, 0]
            readonly property bool focused: shotWindow.focusOn === part
            visible: !!value
            x: b[0] * shotWindow.scale; y: b[1] * shotWindow.scale
            width: b[2] * shotWindow.scale; height: b[3] * shotWindow.scale
            color: "transparent"
            border.color: ink; border.width: focused ? 2 : 1
            opacity: focused ? 1 : 0.75
            Repeater {
                model: partBox.focused ? 8 : 0
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
                            if (partBox.part === "picture") shotWindow.picture = next; else shotWindow.area = next
                            shotWindow.matches = []
                        }
                    }
                }
            }
        }
        PartBox { part: "area"; value: shotWindow.area; ink: shotWindow.areaInk }
        PartBox { id: pictureBox; part: "picture"; value: shotWindow.picture; ink: shotWindow.pictureInk }

        // C held: the saved picture over the new one
        Image {
            visible: shotWindow.comparing && !!shotWindow.picture && !!shotWindow.saved.picture
            source: shotWindow.saved.picture || ""
            x: pictureBox.x; y: pictureBox.y
            width: sourceSize.width * shotWindow.scale; height: sourceSize.height * shotWindow.scale
            opacity: 0.7; smooth: false
        }

        // the point: a crosshair, dragged to move it
        Item {
            id: pointMark
            visible: !!shotWindow.point
            x: (shotWindow.point ? shotWindow.point[0] : 0) * shotWindow.scale
            y: (shotWindow.point ? shotWindow.point[1] : 0) * shotWindow.scale
            Rectangle { x: -1; y: -12; width: 2; height: 24; color: shotWindow.pointInk }
            Rectangle { x: -12; y: -1; width: 24; height: 2; color: shotWindow.pointInk }
            Rectangle { x: -7; y: -7; width: 14; height: 14; radius: 7; color: "transparent"; border.color: shotWindow.pointInk; border.width: shotWindow.focusOn === "point" ? 3 : 2 }
            MouseArea {
                x: -12; y: -12; width: 24; height: 24
                cursorShape: Qt.SizeAllCursor
                onPressed: { shotWindow.remember(); shotWindow.focusOn = "point" }
                onPositionChanged: function (mouse) {
                    if (!pressed) return
                    var at = mapToItem(shot, mouse.x, mouse.y)
                    shotWindow.point = shotWindow.toShot(at.x, at.y)
                }
            }
        }

        // readouts: click one to type exact numbers
        component Readout: Rectangle {
            id: readout
            property string text: ""
            property string value: ""   // the numbers to edit, "x, y, w, h"
            property color ink: studio.colors.text
            signal edited(var numbers)
            height: 24; radius: 12
            width: editing ? 190 : label.implicitWidth + 18
            color: studio.colors.glassStrong; border.color: studio.colors.line
            property bool editing: false
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
            visible: !!shotWindow.picture
            x: pictureBox.x + pictureBox.width + 10; y: pictureBox.y
            ink: shotWindow.pictureInk
            text: shotWindow.picture ? "picture " + shotWindow.picture[2] + " × " + shotWindow.picture[3] : ""
            value: shotWindow.picture ? shotWindow.picture.join(", ") : ""
            onEdited: function (numbers) { if (numbers.length === 4) shotWindow.setPart("picture", shotWindow.clamp(numbers)) }
        }
        Readout {
            visible: !!shotWindow.point
            x: pointMark.x + 18; y: pointMark.y + (shotWindow.picture ? 10 : -12)
            ink: shotWindow.pointInk
            readonly property var centre: shotWindow.picture ? [shotWindow.picture[0] + shotWindow.picture[2] / 2, shotWindow.picture[1] + shotWindow.picture[3] / 2] : null
            readonly property var offset: centre && shotWindow.point ? [Math.round(shotWindow.point[0] - centre[0]), Math.round(shotWindow.point[1] - centre[1])] : null
            text: !shotWindow.point ? "" : offset ? "click " + (offset[0] >= 0 ? "+" : "") + offset[0] + ", " + (offset[1] >= 0 ? "+" : "") + offset[1] + " from its centre" : "point " + shotWindow.point[0] + ", " + shotWindow.point[1]
            value: !shotWindow.point ? "" : offset ? offset.join(", ") : shotWindow.point.join(", ")
            onEdited: function (numbers) {
                if (numbers.length !== 2) return
                shotWindow.setPart("point", centre ? [centre[0] + numbers[0], centre[1] + numbers[1]] : numbers)
            }
        }
        Readout {
            visible: !!shotWindow.area
            x: (shotWindow.area ? shotWindow.area[0] : 0) * shotWindow.scale
            y: (shotWindow.area ? shotWindow.area[1] + shotWindow.area[3] : 0) * shotWindow.scale + 8
            readonly property bool holds: !!shotWindow.area && !!shotWindow.picture && shotWindow.inside(shotWindow.area, shotWindow.picture)
            ink: shotWindow.picture && !holds ? studio.colors.warn : shotWindow.areaInk
            text: !shotWindow.area ? "" : "area " + shotWindow.area.join(", ").replace(/, (\d+), (\d+)$/, " · $1 × $2")
                + (shotWindow.picture ? (holds ? " · picture inside ✓" : " · picture outside ⚠") : "")
            value: shotWindow.area ? shotWindow.area.join(", ") : ""
            onEdited: function (numbers) { if (numbers.length === 4) shotWindow.setPart("area", shotWindow.clamp(numbers)) }
        }

        // Test's scan: a line sweeps the searched area, then the matches show
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

        // the guide's next picture, top right; it slides away with the pill
        Rectangle {
            visible: shotWindow.current !== null
            anchors.right: parent.right; anchors.rightMargin: 24
            y: shotWindow.tucked ? -height - 10 : 24
            Behavior on y { NumberAnimation { duration: studio.effects ? 200 : 0; easing.type: Easing.OutCubic } }
            width: 380; height: guide.implicitHeight + 32; radius: 16
            color: studio.colors.glassStrong; border.color: studio.colors.line
            Column {
                id: guide
                x: 18; y: 16; width: parent.width - 36; spacing: 8
                RowLayout {
                    width: parent.width
                    Text { text: shotWindow.current ? (shotWindow.current.screen || "Next picture") : ""; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold; Layout.fillWidth: true }
                    Text { text: capture.items.length + " left"; color: studio.colors.muted; font.pixelSize: 13 }
                }
                Row {
                    spacing: 8
                    Chip { text: shotWindow.current ? shotWindow.current.kind : ""; tone: "accent" }
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
                    model: [{ box: shotWindow.area, ink: shotWindow.areaInk }, { box: shotWindow.picture, ink: shotWindow.pictureInk }]
                    delegate: Rectangle {
                        required property var modelData
                        visible: !!modelData.box
                        x: modelData.box ? magnifier.px(modelData.box[0], 0) : 0; y: modelData.box ? magnifier.px(modelData.box[1], 1) : 0
                        width: modelData.box ? modelData.box[2] * magnifier.zoom : 0; height: modelData.box ? modelData.box[3] * magnifier.zoom : 0
                        color: "transparent"; border.color: modelData.ink; border.width: 2
                    }
                }
                Rectangle {
                    visible: !!shotWindow.point
                    x: shotWindow.point ? magnifier.px(shotWindow.point[0], 0) : 0; y: shotWindow.point ? magnifier.px(shotWindow.point[1], 1) : 0
                    width: magnifier.zoom; height: magnifier.zoom
                    color: "transparent"; border.color: shotWindow.pointInk; border.width: 2
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
                color: studio.colors.glassStrong
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
                // the pill: the top edge brings it back; away from it, it slides up after a few seconds
                var near = p.y <= pillZone.y + pillZone.height + 24 && p.x >= pillZone.x - 24 && p.x <= pillZone.x + pillZone.width + 24
                if (shotWindow.tucked) { if (p.y <= 4) shotWindow.showPill() }
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

        // ---- the pill, top centre: the name, the target's three parts, undo and redo, Test, Save; and under it the
        // one line that matters now. It slides up out of the way and leaves a sliver.
        Item {
            id: pillZone
            width: pill.width
            height: pill.height + 10 + under.height
            x: (stage.width - width) / 2
            y: shotWindow.tucked ? -pill.height - 10 - under.height + 5 : 14
            Behavior on y { NumberAnimation { duration: studio.effects ? 200 : 0; easing.type: Easing.OutCubic } }
            HoverHandler { onHoveredChanged: if (hovered) tuckTimer.stop() }

            Rectangle {
                id: pill
                width: bar.implicitWidth + 16; height: 56; radius: 28
                color: studio.colors.glassStrong; border.color: studio.colors.line
                RowLayout {
                    id: bar
                    anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
                    spacing: 6
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
                        onEditingFinished: if (!shotWindow.picture && !shotWindow.area && !shotWindow.point) shotWindow.takeSaved(text.trim())
                        Keys.onEscapePressed: capture.close()
                        background: Rectangle { radius: 20; color: studio.colors.raised; border.color: nameField.activeFocus ? studio.colors.accent : "transparent" }
                    }
                    Repeater {
                        model: [
                            { part: "picture", label: "Picture", glyph: "▣", ink: shotWindow.pictureInk, how: "Drag or click it · again for bigger, right-click smaller" },
                            { part: "area", label: "Area", glyph: "⬚", ink: shotWindow.areaInk, how: "Shift+drag the area it's searched in (none: the whole screen)" },
                            { part: "point", label: "Point", glyph: "✛", ink: shotWindow.pointInk, how: "Ctrl+click where to click it (none: its centre)" }
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            readonly property bool made: !!shotWindow.partOf(modelData.part)
                            readonly property bool on: shotWindow.focusOn === modelData.part
                            Layout.preferredHeight: 32
                            Layout.preferredWidth: chipRow.implicitWidth + 22
                            radius: 16
                            color: made ? Qt.rgba(modelData.ink.r, modelData.ink.g, modelData.ink.b, on ? 0.28 : 0.14) : "transparent"
                            border.color: Qt.rgba(modelData.ink.r, modelData.ink.g, modelData.ink.b, made ? 0.9 : 0.4)
                            border.width: on ? 2 : 1
                            Row {
                                id: chipRow
                                anchors.centerIn: parent; spacing: 6
                                Text { text: modelData.glyph; color: modelData.ink; font.pixelSize: 12; font.family: studio.symbols; anchors.verticalCenter: parent.verticalCenter }
                                Text { text: modelData.label; color: made ? modelData.ink : studio.colors.muted; font.pixelSize: 12; font.weight: Font.DemiBold; anchors.verticalCenter: parent.verticalCenter }
                            }
                            MouseArea {
                                id: chipArea
                                anchors.fill: parent; hoverEnabled: true
                                acceptedButtons: Qt.LeftButton | Qt.RightButton
                                cursorShape: Qt.PointingHandCursor
                                onClicked: function (mouse) {
                                    if (mouse.button === Qt.RightButton) shotWindow.drop(modelData.part)
                                    else { shotWindow.focusOn = modelData.part; if (!made) shotWindow.say(modelData.how, false) }
                                    stage.forceActiveFocus()
                                }
                            }
                            ToolTip.visible: chipArea.containsMouse
                            ToolTip.delay: 400
                            ToolTip.text: modelData.how + (made ? " · right-click drops it" : "")
                        }
                    }
                    Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
                    IconButton { glyph: "↶"; tip: "Undo (Ctrl+Z)"; enabled: shotWindow.past.length > 0; onClicked: shotWindow.undo() }
                    IconButton { glyph: "↷"; tip: "Redo (Ctrl+Y)"; enabled: shotWindow.future.length > 0; onClicked: shotWindow.redo() }
                    Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
                    PillButton { small: true; icon: "⌕"; text: "Test"; enabled: !!shotWindow.picture; onClicked: shotWindow.test() }
                    IconButton { glyph: "✕"; tip: "Close (Esc)"; onClicked: capture.close() }
                    PillButton { kind: "primary"; small: true; text: "Save"; onClicked: shotWindow.save() }
                }
            }
            Column {
                id: under
                anchors { horizontalCenter: pill.horizontalCenter; top: pill.bottom; topMargin: 10 }
                spacing: 8
                Chip {
                    anchors.horizontalCenter: parent.horizontalCenter
                    tone: shotWindow.note === "" ? "plain" : shotWindow.noteBad ? "warn" : "ok"
                    text: shotWindow.note !== "" ? shotWindow.note
                        : "drag a picture · Shift+drag its area · Ctrl+click where to click · Tab: the next part · T tests · Ctrl+Z undoes"
                }
                // after Test: the similarity a match needs; matches under it fade
                Rectangle {
                    visible: shotWindow.matches.length > 0
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 330; height: 44; radius: 22
                    color: studio.colors.glassStrong; border.color: studio.colors.line
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
