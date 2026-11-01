// Capture: the frozen screen, full screen. Click to box what's there (again for bigger, right-click smaller),
// or drag a box; the handles and the arrow keys change it. Test marks every match with its score; Enter saves.
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

    property string kind: "image"          // image, region, point
    property var box: null                  // [x, y, w, h] in the shot's pixels
    property var point: null                // [x, y]
    property var boxes: []                  // the candidates around the last click, smallest first
    property int chosen: 0
    property var lastClick: null
    property var matches: []
    property var waiting: null  // Test's answer while the scan sweeps the searched area
    property real similarity: 0.9  // after Test: matches under it fade
    property string note: ""
    property bool noteBad: false
    readonly property real scale: Math.min(width / Math.max(1, capture.shotWidth), height / Math.max(1, capture.shotHeight))
    readonly property var current: capture.items.length > 0 ? capture.items[0] : null

    onVisibleChanged: if (visible) { reset(); nameField.text = current ? current.name : ""; nameField.forceActiveFocus() }
    onCurrentChanged: if (current) { nameField.text = current.name; kind = current.kind === "region" ? "region" : current.kind === "point" ? "point" : "image" }

    function reset() { box = null; point = null; boxes = []; matches = []; waiting = null; note = ""; lastClick = null }
    function toShot(x, y) { return [Math.round(x / scale), Math.round(y / scale)] }
    function clamp(next) {
        var x = Math.max(0, Math.min(next[0], capture.shotWidth - 1)), y = Math.max(0, Math.min(next[1], capture.shotHeight - 1))
        return [x, y, Math.max(1, Math.min(next[2], capture.shotWidth - x)), Math.max(1, Math.min(next[3], capture.shotHeight - y))]
    }
    function say(text, bad) { note = text; noteBad = !!bad }

    function clicked(x, y, bigger) {
        var at = toShot(x, y)
        if (kind === "point") { point = at; return }
        var same = lastClick && Math.abs(lastClick[0] - at[0]) < 4 && Math.abs(lastClick[1] - at[1]) < 4
        if (!same) {
            var found = capture.candidates(at[0], at[1], kind)
            boxes = found.boxes; chosen = found.start || 0; lastClick = at
        } else if (boxes.length) {
            chosen = Math.max(0, Math.min(boxes.length - 1, chosen + (bigger ? 1 : -1)))
        }
        if (boxes.length) { box = boxes[chosen]; matches = [] }
    }
    function test() {
        if (!box) { say("Box something first", true); return }
        var found = capture.test(box, null)
        if (found.error) { say(found.error, true); return }
        matches = []
        note = ""
        waiting = found
        if (studio.effects && found.searched) scan.sweep(found.searched)
        else showFound()
    }
    // what Test found: the box itself counts once; look-alikes are the other places, scoring under the line
    function showFound() {
        var found = waiting
        waiting = null
        if (!found) return
        matches = found.matches || []
        var strong = matches.filter(function (match) { return match.score >= shotWindow.similarity }).length
        var others = matches.length - strong
        var where = strong === 0 ? "Not found" : strong === 1 ? "Found once" : "Found " + strong + " times"
        var alike = others === 0 ? "nothing else close" : others === 1 ? "1 look-alike under the line" : others + " look-alikes under the line"
        say(where + " at " + shotWindow.similarity.toFixed(2) + " · " + alike + " · " + found.ms + " ms", strong !== 1)
    }
    function save() {
        var name = nameField.text.trim()
        var result = capture.save(name, kind, kind === "image" ? box : null, kind === "region" ? box : null, point)
        if (result.error) { say(result.error, true); return }
        say(result.message || ("Saved " + name), !!result.risky)
        reset()
        nameField.text = current ? current.name : ""
    }
    function nudge(dx, dy, grow) {
        if (!box) return
        box = clamp(grow ? [box[0], box[1], box[2] + dx, box[3] + dy] : [box[0] + dx, box[1] + dy, box[2], box[3]])
        matches = []
    }

    Item {
        id: stage
        anchors.fill: parent
        focus: true
        Keys.onPressed: function (event) {
            var step = (event.modifiers & Qt.ShiftModifier) ? 10 : 1
            var grow = (event.modifiers & Qt.ControlModifier) !== 0
            if (event.key === Qt.Key_Escape) capture.close()
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) shotWindow.save()
            else if (event.key === Qt.Key_T) shotWindow.test()
            else if (event.key === Qt.Key_Left) shotWindow.nudge(-step, 0, grow)
            else if (event.key === Qt.Key_Right) shotWindow.nudge(step, 0, grow)
            else if (event.key === Qt.Key_Up) shotWindow.nudge(0, -step, grow)
            else if (event.key === Qt.Key_Down) shotWindow.nudge(0, step, grow)
            else return
            event.accepted = true
        }

        Image {
            id: shot
            source: capture.source
            width: capture.shotWidth * shotWindow.scale; height: capture.shotHeight * shotWindow.scale
            smooth: true
        }

        // the shot outside the box, dimmed to 42% (the design system's screen-dim): above, below, left, right
        Item {
            id: dim
            visible: !!shotWindow.box
            readonly property var b: shotWindow.box ? shotWindow.box.map(function (v) { return Math.round(v * shotWindow.scale) }) : [0, 0, 0, 0]
            anchors.fill: shot
            Rectangle { color: Qt.rgba(0, 0, 0, 0.58); x: 0; y: 0; width: dim.width; height: dim.b[1] }
            Rectangle { color: Qt.rgba(0, 0, 0, 0.58); x: 0; y: dim.b[1] + dim.b[3]; width: dim.width; height: dim.height - y }
            Rectangle { color: Qt.rgba(0, 0, 0, 0.58); x: 0; y: dim.b[1]; width: dim.b[0]; height: dim.b[3] }
            Rectangle { color: Qt.rgba(0, 0, 0, 0.58); x: dim.b[0] + dim.b[2]; y: dim.b[1]; width: dim.width - x; height: dim.b[3] }
        }

        MouseArea {
            anchors.fill: shot
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            property var from: null
            property bool dragged: false
            onPressed: function (mouse) { from = [mouse.x, mouse.y]; dragged = false; stage.forceActiveFocus() }
            onPositionChanged: function (mouse) {
                if (!from || shotWindow.kind === "point" || mouse.buttons !== Qt.LeftButton) return
                if (!dragged && Math.abs(mouse.x - from[0]) + Math.abs(mouse.y - from[1]) < 6) return
                dragged = true
                var a = shotWindow.toShot(Math.min(from[0], mouse.x), Math.min(from[1], mouse.y))
                var b = shotWindow.toShot(Math.max(from[0], mouse.x), Math.max(from[1], mouse.y))
                shotWindow.box = shotWindow.clamp([a[0], a[1], b[0] - a[0], b[1] - a[1]])
                shotWindow.boxes = []; shotWindow.lastClick = null; shotWindow.matches = []
            }
            onReleased: function (mouse) {
                if (!dragged) shotWindow.clicked(mouse.x, mouse.y, mouse.button === Qt.LeftButton)
                from = null
            }
        }

        // the box, its size and its handles
        Rectangle {
            id: frame
            visible: !!shotWindow.box
            readonly property var b: shotWindow.box || [0, 0, 0, 0]
            x: b[0] * shotWindow.scale; y: b[1] * shotWindow.scale
            width: b[2] * shotWindow.scale; height: b[3] * shotWindow.scale
            color: "transparent"
            border.color: shotWindow.kind === "region" ? studio.colors.accent2 : studio.colors.accent
            border.width: 2
            Repeater {
                model: 8
                delegate: Rectangle {
                    required property int index
                    readonly property real fx: [0, 0.5, 1, 1, 1, 0.5, 0, 0][index]
                    readonly property real fy: [0, 0, 0, 0.5, 1, 1, 1, 0.5][index]
                    x: frame.width * fx - 5; y: frame.height * fy - 5
                    width: 10; height: 10; radius: 2
                    color: "white"; border.color: frame.border.color
                    MouseArea {
                        anchors.fill: parent; anchors.margins: -4
                        cursorShape: (index % 4 === 1) ? Qt.SizeVerCursor : (index % 4 === 3) ? Qt.SizeHorCursor : (index === 0 || index === 4) ? Qt.SizeFDiagCursor : Qt.SizeBDiagCursor
                        onPositionChanged: function (mouse) {
                            if (!pressed) return
                            var at = mapToItem(shot, mouse.x, mouse.y), p = shotWindow.toShot(at.x, at.y), b = shotWindow.box
                            var left = b[0], top = b[1], right = b[0] + b[2], bottom = b[1] + b[3]
                            if (fx === 0) left = Math.min(p[0], right - 1)
                            if (fx === 1) right = Math.max(p[0], left + 1)
                            if (fy === 0) top = Math.min(p[1], bottom - 1)
                            if (fy === 1) bottom = Math.max(p[1], top + 1)
                            shotWindow.box = shotWindow.clamp([left, top, right - left, bottom - top])
                            shotWindow.matches = []
                        }
                    }
                }
            }
            Chip {
                anchors { left: parent.left; top: parent.bottom; topMargin: 8 }
                tone: "accent"
                text: frame.b[2] + " × " + frame.b[3]
            }
        }

        // the point
        Rectangle {
            visible: !!shotWindow.point
            x: (shotWindow.point ? shotWindow.point[0] : 0) * shotWindow.scale - 8
            y: (shotWindow.point ? shotWindow.point[1] : 0) * shotWindow.scale - 8
            width: 16; height: 16; radius: 8
            color: "transparent"; border.color: studio.colors.ok; border.width: 3
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

        // the hint, top left
        Rectangle {
            x: 24; y: 24; height: 36; radius: 18
            width: hint.implicitWidth + 28
            color: studio.colors.glassStrong; border.color: studio.colors.line
            Text {
                id: hint; anchors.centerIn: parent
                text: shotWindow.kind === "point" ? "click the point · Esc closes"
                    : "click to box · again for bigger, right-click smaller · drag a box · arrows move it, Ctrl+arrows size it · T tests"
                color: studio.colors.muted; font.pixelSize: 12
            }
        }

        // the guide's next picture, top right
        Rectangle {
            visible: shotWindow.current !== null
            anchors { right: parent.right; top: parent.top; margins: 24 }
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

        // the toolbar, bottom centre: the name, the kind, Test, Save (the shared pill of darbit's tools)
        Rectangle {
            id: toolbar
            anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 36 }
            height: 58; radius: 29
            width: bar.implicitWidth + 20
            color: studio.colors.glassStrong; border.color: studio.colors.line
            RowLayout {
                id: bar
                anchors { left: parent.left; leftMargin: 10; verticalCenter: parent.verticalCenter }
                spacing: 8
                TextField {
                    id: nameField
                    placeholderText: "Name, e.g. Lobby.Play"
                    placeholderTextColor: studio.colors.faint
                    Layout.preferredWidth: 230; Layout.preferredHeight: 40
                    leftPadding: 16
                    color: studio.colors.text
                    font.pixelSize: 14; font.weight: Font.DemiBold
                    onAccepted: shotWindow.save()
                    Keys.onEscapePressed: capture.close()
                    background: Rectangle { radius: 20; color: studio.colors.raised; border.color: nameField.activeFocus ? studio.colors.accent : "transparent" }
                }
                Segmented {
                    itemHeight: 32
                    current: shotWindow.kind
                    model: [{ key: "image", label: "Image" }, { key: "region", label: "Area" }, { key: "point", label: "Point" }]
                    onPicked: function (key) {
                        shotWindow.kind = key
                        if (key === "point") shotWindow.box = null
                        else shotWindow.point = null
                        stage.forceActiveFocus()
                    }
                }
                Rectangle { width: 1; height: 26; color: studio.colors.line }
                PillButton { small: true; icon: "⌕"; text: "Test"; enabled: shotWindow.kind === "image" && !!shotWindow.box; onClicked: shotWindow.test() }
                IconButton { glyph: "✕"; tip: "Close (Esc)"; onClicked: capture.close() }
                PillButton { kind: "primary"; small: true; text: "Save"; onClicked: shotWindow.save() }
            }
        }
        // after Test: the similarity a match needs; matches under it fade
        Rectangle {
            visible: shotWindow.matches.length > 0
            anchors { horizontalCenter: toolbar.horizontalCenter; bottom: toolbar.top; bottomMargin: 44 }
            width: 330; height: 44; radius: 22
            color: studio.colors.glassStrong; border.color: studio.colors.line
            Row {
                anchors.centerIn: parent; spacing: 12
                Text { text: "needs"; color: studio.colors.muted; font.pixelSize: 13; anchors.verticalCenter: parent.verticalCenter }
                Slider {
                    id: needs
                    width: 180; from: 0.6; to: 1.0; value: shotWindow.similarity
                    onMoved: shotWindow.similarity = Math.round(value * 100) / 100
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text { text: shotWindow.similarity.toFixed(2); color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold; anchors.verticalCenter: parent.verticalCenter }
            }
        }

        // the magnifier: the shot's own pixels, each `zoom` points wide (Ctrl+wheel: 2 to 24), the pixel under the
        // mouse framed, and its place and colour below; it flips near the edges
        Item {
            id: magnifier
            objectName: "magnifier"
            readonly property int size: 150
            property real zoom: 8
            property point at: Qt.point(-1, -1)  // in the shot's pixels
            visible: at.x >= 0 && !toolbar.contains(toolbar.mapFromItem(stage, hoverPoint.x, hoverPoint.y))
            property point hoverPoint: Qt.point(0, 0)
            x: hoverPoint.x + 24 + size > stage.width ? hoverPoint.x - size - 24 : hoverPoint.x + 24
            y: hoverPoint.y + 24 + size + 26 > stage.height ? hoverPoint.y - size - 50 : hoverPoint.y + 24
            width: size; height: size + 26
            Rectangle {
                width: magnifier.size; height: magnifier.size; radius: 14
                color: "black"; border.color: studio.colors.accent; border.width: 2
                clip: true
                Image {  // the shot itself, not smoothed: each of its pixels a square of its own colour
                    source: capture.source
                    smooth: false; mipmap: false
                    width: capture.shotWidth * magnifier.zoom; height: capture.shotHeight * magnifier.zoom
                    x: magnifier.size / 2 - (magnifier.at.x + 0.5) * magnifier.zoom
                    y: magnifier.size / 2 - (magnifier.at.y + 0.5) * magnifier.zoom
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
                    anchors.centerIn: parent; spacing: 8
                    Text { text: magnifier.at.x + ", " + magnifier.at.y + "  " + magnifier.zoom + "×"; color: studio.colors.text; font.family: "monospace"; font.pixelSize: 11 }
                    Rectangle { width: 10; height: 10; radius: 2; color: swatch.text || "transparent"; anchors.verticalCenter: parent.verticalCenter }
                    Text { id: swatch; text: magnifier.at.x >= 0 ? capture.colour(magnifier.at.x, magnifier.at.y) : ""; color: studio.colors.muted; font.family: "monospace"; font.pixelSize: 11 }
                }
            }
        }
        HoverHandler {
            target: stage
            onPointChanged: {
                magnifier.hoverPoint = point.position
                // the pixel the mouse is on, not the nearest corner
                magnifier.at = Qt.point(Math.min(capture.shotWidth - 1, Math.floor(point.position.x / shotWindow.scale)),
                                        Math.min(capture.shotHeight - 1, Math.floor(point.position.y / shotWindow.scale)))
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
        Chip {
            visible: shotWindow.note !== ""
            anchors { horizontalCenter: toolbar.horizontalCenter; bottom: toolbar.top; bottomMargin: 10 }
            tone: shotWindow.noteBad ? "warn" : "ok"
            text: shotWindow.note
        }
    }
}
