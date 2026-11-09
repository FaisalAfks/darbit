// One block of the Overview (round 14): a card drawn by its kind from what its `shows` holds now. In Customize mode it
// has a grip to drag it elsewhere, a corner to make it wider or narrower, and ✕ to take it off.
import QtQuick
import QtQuick.Layouts
import "format.js" as Format
import "motion.js" as Motion

Glass {
    id: block
    property var spec: ({})        // {kind, shows, title, width, origin}
    property var info: null        // what `shows` holds now (server/overview.py data)
    property bool editing: false
    property real unit: 80         // the width of one of the row's 12 parts
    property real gap: 16
    signal moved(real sceneX, real sceneY)
    signal resized(int width)
    signal removed()
    readonly property string kind: spec.kind || "text"
    readonly property bool running: studio.bot.status === "running" || studio.bot.status === "paused"
    title: kind === "now" ? "" : (spec.title || spec.shows || "")
    note: spec.origin && spec.origin !== "darbit" && !editing ? spec.origin : ""
    lift: !editing
    implicitHeight: (title !== "" ? 64 : 44) + (shown.item ? shown.item.implicitHeight : 0)
    border.color: editing ? Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.55)
        : hovered && lift ? hoverEdge : studio.colors.line

    content: Loader {
        id: shown
        width: parent.width
        sourceComponent: block.info === null || block.info === undefined ? nothingYet
            : block.kind === "now" ? nowView : block.kind === "round" ? roundView : block.kind === "ring" ? ringView
            : block.kind === "number" ? numberView : block.kind === "chart" ? chartView : block.kind === "list" ? listView
            : block.kind === "screen" ? screenView : block.kind === "button" ? buttonView
            : block.kind === "recoveries" ? recoveriesView : textView
    }

    // ---- Customize: the grip, ✕ and the corner
    Row {
        visible: block.editing
        anchors { right: parent.right; top: parent.top; margins: 8 }
        spacing: 4
        IconButton { width: 28; height: 28; glyph: "✕"; tip: "Take it off the Overview"; onClicked: block.removed() }
    }
    Text {
        visible: block.editing
        x: 8; y: 6; text: "⋮⋮"; color: studio.colors.faint; font.pixelSize: 13
        HoverHandler { cursorShape: Qt.SizeAllCursor }
    }
    DragHandler {
        id: dragging
        enabled: block.editing
        target: block
        onActiveChanged: if (!active) { var at = block.mapToItem(null, block.width / 2, block.height / 2); block.moved(at.x, at.y) }
    }
    z: dragging.active ? 10 : 0
    dim: dragging.active ? 0.85 : 1
    Rectangle {
        visible: block.editing
        anchors { right: parent.right; bottom: parent.bottom; margins: 5 }
        width: 14; height: 14; color: "transparent"
        Rectangle { anchors.right: parent.right; anchors.bottom: parent.bottom; width: 12; height: 2; color: studio.colors.accent }
        Rectangle { anchors.right: parent.right; anchors.bottom: parent.bottom; width: 2; height: 12; color: studio.colors.accent }
        MouseArea {
            anchors.fill: parent; anchors.margins: -6
            cursorShape: Qt.SizeHorCursor
            property real from: 0
            property int startWidth: 4
            onPressed: function (mouse) { from = mapToItem(null, mouse.x, 0).x; startWidth = block.spec.width || 4 }
            onReleased: function (mouse) {
                var moved = mapToItem(null, mouse.x, 0).x - from
                var wanted = startWidth + Math.round(moved / (block.unit + block.gap))
                var widths = [3, 4, 6, 8, 12], best = widths[0]
                for (var index = 0; index < widths.length; index++)
                    if (Math.abs(widths[index] - wanted) < Math.abs(best - wanted)) best = widths[index]
                if (best !== startWidth) block.resized(best)
            }
        }
    }

    // whether the bot's darbit.toml declares this mode, so it can run alone
    function declares(mode) {
        var modes = studio.bot.modes || []
        for (var index = 0; index < modes.length; index++)
            if (modes[index].name === mode) return true
        return false
    }

    // ---- the kinds
    Component { id: nothingYet; Text { width: parent ? parent.width : 0; text: "Nothing yet today."; color: studio.colors.faint; font.pixelSize: 13 } }
    Component {
        id: nowView
        Column {
            id: nowColumn
            width: parent ? parent.width : 0
            spacing: 8
            readonly property var steps: block.info && block.info.path ? block.info.path.map(function (step) { return String(step).split(" > ").pop() }) : []
            Text {
                text: block.running ? "NOW · " + (studio.bot.status === "paused" ? "PAUSED" : "RUNNING " + Format.duration(studio.now - (studio.bot.since || studio.now)).toUpperCase()) : "NOW"
                color: studio.bot.status === "paused" ? studio.colors.warn : block.running ? studio.colors.ok : studio.colors.muted
                font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.3
            }
            Flow {
                width: parent.width; spacing: 10
                Repeater {
                    model: nowColumn.steps.length ? nowColumn.steps : [block.running ? "Starting…" : "Not running"]
                    delegate: Row {
                        required property var modelData
                        required property int index
                        spacing: 10
                        Text { visible: index > 0; text: "›"; color: studio.colors.faint; font.pixelSize: 26; anchors.verticalCenter: parent.verticalCenter }
                        Text { text: modelData; color: index === nowColumn.steps.length - 1 ? studio.colors.accent : studio.colors.text; font.pixelSize: 28; font.weight: Font.Bold }
                    }
                }
            }
            Text {
                width: parent.width; elide: Text.ElideRight
                text: block.info && block.info.since ? "since " + Format.clock(block.info.since) + " · " + Format.duration(Format.since(block.info.since, studio.now)) + " in this step"
                    : block.running ? "" : "Press Play to start " + (studio.bot.name || "the bot") + ", or start it from a terminal: this page follows it either way."
                color: studio.colors.muted; font.pixelSize: 13
            }
        }
    }
    Component {
        id: roundView
        Column {
            width: parent ? parent.width : 0
            Repeater {
                model: block.info.steps || []
                delegate: Item {
                    id: roundRow
                    required property var modelData
                    // a mode the bot declares can run alone (#318): ▶ on hover while the bot is stopped
                    readonly property bool runnable: !block.running && !block.editing && block.declares(modelData.name)
                    width: parent.width; height: 40
                    HoverHandler { id: rowHover; enabled: roundRow.runnable }
                    Rectangle {  // the hover's light, a little wider than the row so its dot and text stay put
                        x: -10; width: parent.width + 20; height: parent.height; radius: 10
                        visible: roundRow.runnable && rowHover.hovered
                        color: studio.colors.raised
                    }
                    RowLayout {
                        anchors.fill: parent; spacing: 12
                        Rectangle {
                            width: 10; height: 10; radius: 5
                            color: modelData.state === "ok" ? studio.colors.ok : modelData.state === "running" ? studio.colors.accent
                                : modelData.state === "failed" ? studio.colors.danger : studio.colors.faint
                        }
                        Text { text: modelData.name; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.fillWidth: true; elide: Text.ElideRight }
                        Text {
                            text: modelData.state === "planned" ? "later" : modelData.state === "running" ? "running"
                                : modelData.state === "failed" ? (modelData.reason || "failed")
                                : Format.clock(modelData.started) + (modelData.seconds ? " · " + Format.duration(modelData.seconds) : "")
                            color: modelData.state === "running" ? studio.colors.accent : modelData.state === "failed" ? studio.colors.danger : studio.colors.muted
                            font.pixelSize: 12
                        }
                        PillButton {
                            objectName: "runOnly"
                            visible: roundRow.runnable && rowHover.hovered
                            kind: "primary"; small: true; icon: "▶"
                            implicitWidth: 24; implicitHeight: 24
                            onClicked: studio.playOnly(roundRow.modelData.name, "")
                        }
                    }
                }
            }
        }
    }
    Component {
        id: ringView
        Item {
            width: parent ? parent.width : 0; implicitHeight: 128
            Ring {
                anchors.centerIn: parent
                width: 118; height: 118; thickness: 10
                done: Number(block.info.done !== undefined ? block.info.done : block.info.value) || 0
                total: Number(block.info.total) || 1
            }
        }
    }
    Component {
        id: numberView
        Column {
            id: numberColumn
            width: parent ? parent.width : 0; spacing: 4
            readonly property bool gain: block.info.today !== undefined
            Text {
                // inside the text, not the column: the column would leave room for it
                CountUp { id: counted; to: numberColumn.gain ? Number(block.info.today) : typeof block.info.value === "number" ? block.info.value : NaN }
                text: (counted.counting ? (numberColumn.gain ? "+" + Number(counted.value).toLocaleString(Qt.locale(), "f", 0) : Format.setting(Math.round(counted.value)))
                    : numberColumn.gain ? "+" + Number(block.info.today).toLocaleString(Qt.locale(), "f", 0) : Format.setting(block.info.value)) + (block.info.unit ? " " + block.info.unit : "")
                color: block.info.today !== undefined ? studio.colors.ok : studio.colors.text; font.pixelSize: 30; font.weight: Font.Bold
            }
            Text {
                visible: text !== ""
                width: parent.width; elide: Text.ElideRight
                text: block.info.sub || (block.info.total !== null && block.info.total !== undefined ? "total " + Number(block.info.total).toLocaleString(Qt.locale(), "f", 0) : "")
                color: studio.colors.muted; font.pixelSize: 12
            }
        }
    }
    Component {
        id: chartView
        Item {
            width: parent ? parent.width : 0; implicitHeight: 90
            readonly property var week: block.info.week || []
            readonly property real most: Math.max.apply(null, week.concat([1]))
            Row {
                anchors.bottom: parent.bottom; width: parent.width; height: 80; spacing: 6
                Repeater {
                    model: parent.parent.week
                    delegate: Rectangle {
                        id: bar
                        required property var modelData
                        required property int index
                        anchors.bottom: parent.bottom
                        width: (parent.width - 6 * 6) / 7; radius: 4
                        height: Math.max(3, 76 * modelData / parent.parent.most)
                        color: index === 6 ? studio.colors.accent : studio.colors.accent2
                        opacity: index === 6 ? 1 : 0.55
                        // each bar grows from the bottom when the page shows, one after another
                        property real grown: 1
                        transform: Scale { origin.y: bar.height; yScale: bar.grown }
                        function grow() {
                            if (!studio.motion.on) { growing.stop(); grown = 1; return }
                            grown = 0
                            growing.wait = studio.motion.growDelay + index * studio.motion.growStagger
                            growing.restart()
                        }
                        onVisibleChanged: if (visible) grow(); else { growing.stop(); grown = 1 }
                        Component.onCompleted: if (Motion.fresh()) grow()
                        SequentialAnimation {
                            id: growing
                            property int wait: 0
                            PauseAnimation { duration: growing.wait }
                            NumberAnimation { target: bar; property: "grown"; to: 1; duration: studio.motion.grow; easing.type: Easing.BezierSpline; easing.bezierCurve: studio.motion.spring }
                        }
                    }
                }
            }
        }
    }
    Component {
        id: listView
        Column {
            width: parent ? parent.width : 0
            readonly property var rows: Array.isArray(block.info) ? block.info : Array.isArray(block.info.value) ? block.info.value : (block.info.items || [])
            Text { visible: parent.rows.length === 0; text: "Nothing yet today."; color: studio.colors.faint; font.pixelSize: 13 }
            Repeater {
                model: parent.rows.slice(0, 8)
                delegate: RowLayout {
                    required property var modelData
                    width: parent.width; height: 34; spacing: 10
                    readonly property bool pair: Array.isArray(modelData)
                    Text {
                        Layout.fillWidth: true; elide: Text.ElideRight
                        text: pair ? String(modelData[0]) : typeof modelData === "object" ? (modelData.label || modelData.name || modelData.step || modelData.text || "") : String(modelData)
                        color: studio.colors.text; font.pixelSize: 13; font.weight: Font.DemiBold
                    }
                    Text {
                        text: pair ? String(modelData[1])
                            : modelData.in_seconds !== undefined ? "in " + Format.duration(modelData.in_seconds)
                            : modelData.reason ? modelData.reason
                            : modelData.time ? Format.clock(modelData.time)
                            : modelData.state || ""
                        color: modelData.in_seconds !== undefined ? studio.colors.accent : modelData.reason ? studio.colors.danger : studio.colors.muted
                        font.pixelSize: 12; elide: Text.ElideRight; Layout.maximumWidth: parent.width * 0.55
                    }
                }
            }
        }
    }
    Component {
        id: textView
        Text { width: parent ? parent.width : 0; wrapMode: Text.Wrap; text: Format.setting(block.info.value !== undefined ? block.info.value : block.info) + (block.info.sub ? "\n" + block.info.sub : ""); color: studio.colors.text; font.pixelSize: 15 }
    }
    Component {
        id: screenView
        Rectangle {
            width: parent ? parent.width : 0; implicitHeight: Math.round(width * 9 / 16)
            radius: 10; color: studio.colors.bg; clip: true
            Image { anchors.fill: parent; source: block.info.picture || ""; fillMode: Image.PreserveAspectFit; asynchronous: true; sourceSize.width: 640 }
            Text { visible: !block.info.picture; anchors.centerIn: parent; text: "No screenshot yet"; color: studio.colors.faint; font.pixelSize: 13 }
            MouseArea { anchors.fill: parent; enabled: !!block.info.picture && !block.editing; cursorShape: Qt.PointingHandCursor; onClicked: Qt.openUrlExternally(block.info.picture) }
        }
    }
    Component {
        // how often the bot got itself going again today (d.record.recovered): the count, the most common reason, the
        // last one
        id: recoveriesView
        Column {
            id: recovered
            width: parent ? parent.width : 0; spacing: 6
            readonly property int count: Number(block.info.count) || 0
            readonly property var last: block.info.last || null
            Row {
                spacing: 8
                Text {
                    id: recoveredCount
                    CountUp { id: recoveredCounting; to: recovered.count }
                    text: recoveredCounting.counting ? String(Math.round(recoveredCounting.value)) : recovered.count > 0 ? String(recovered.count) : "None"
                    color: recovered.count > 0 ? studio.colors.warn : studio.colors.ok
                    font.pixelSize: 30; font.weight: Font.Bold
                }
                Text {
                    anchors.baseline: recoveredCount.baseline
                    text: recovered.count === 1 ? "time today" : recovered.count > 1 ? "times today" : "today"
                    color: studio.colors.muted; font.pixelSize: 14
                }
            }
            Text {
                width: parent.width; elide: Text.ElideRight
                text: recovered.count === 0 ? "It hasn't had to recover today."
                    : "mostly " + (block.info.reason || "no reason given") + " (" + block.info.reason_count + " of " + recovered.count + ")"
                color: recovered.count === 0 ? studio.colors.muted : studio.colors.text
                font.pixelSize: 13; font.weight: recovered.count === 0 ? Font.Normal : Font.DemiBold
            }
            Text {
                visible: recovered.last !== null
                width: parent.width; elide: Text.ElideRight
                text: recovered.last ? "last " + Format.clockOf(recovered.last.at) + " · " + recovered.last.how + ": " + recovered.last.why : ""
                color: studio.colors.muted; font.pixelSize: 12
            }
        }
    }
    Component {
        id: buttonView
        Row {
            spacing: 8
            PillButton {
                kind: "primary"; icon: "▶"; text: "Play " + String(block.spec.shows).replace("action:", "")
                enabled: !block.editing
                onClicked: studio.playAction(String(block.spec.shows).replace("action:", ""))
            }
        }
    }
}
