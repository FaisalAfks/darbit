// Scout's pill: the shared pill on a screen edge while Scout is on, like the run pill, in three forms.
// - Docked on the top or bottom: a row with how many images have been seen and a group filter (All, Weak, Not seen
//   yet, Seen); under it (over it at the bottom) a strip of the group's images that scrolls sideways, stepped through
//   with N and Shift+N (or ‹ ›). The one landed on is boxed on the game, with a line saying what's wrong and its retakes.
// - Docked on a side: a ring with how many are seen, then the groups, each folding, in a list that scrolls; a line
//   hovered shows its retakes.
// - Floating: every image in a grid, coloured by its state; one clicked opens in full (ScoutDetail).
// Docked, it slides out of sight a few seconds after the mouse leaves it; the mouse at its edge brings it back. The
// boxes on the game (ScoutWindow) still let every click through.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format
import "scout.js" as Scout

PillWindow {
    id: scoutPill
    hiding: scoutHiding
    place: scoutPlace
    title: "darbit Scout pill"
    cardWidth: 540
    readonly property bool column: form === "column"
    readonly property bool row: form === "row"
    readonly property string seen: "Scout: " + scout.seen + " of " + scout.total + " seen"
    readonly property string took: Math.round(scout.took) + " ms"
    property real now: Date.now() / 1000
    property bool opened: false  // floating: one image in full instead of the grid
    property var folded: ({})    // docked on a side: the groups folded away
    readonly property var landedImage: {
        var images = scout.images
        for (var index = 0; index < images.length; index++)
            if (images[index].name === scout.landed) return images[index]
        return null
    }
    // the one landed on is on screen now (found, or nearly)
    readonly property bool landedHere: scout.boxes.some(function (box) {
        return box.name === scout.landed && box.w && box.score >= box.needs - 0.15
    })
    readonly property var groups: [
        { key: "all", label: "All", count: scout.total },
        { key: "weak", label: "Weak", count: scout.weak, tone: scout.weak > 0 ? "warn" : undefined },
        { key: "not", label: "Not yet", count: scout.notSeen },
        { key: "seen", label: "Seen", count: scout.seen }
    ]
    function key(action) { return studio.keys[action] ? Format.sequence(studio.keys[action]) : "" }
    function retakeOnShot(image) { if (image && image.shot) studio.retakeOn(image.name, "image", image.shot) }
    function retakeNow(image) { if (image) studio.retake(image.name, "image") }
    function open(name) { scout.setGroup("all"); scout.landOn(name); opened = true }
    // a bot with no Images, in the column and the card: made only while it shows, as the pill is always loaded
    Component {
        id: noImages
        EmptyState {
            compact: true; tokens: studio.pillMotion
            width: parent ? parent.width : 420
            glyph: "◎"; title: "No Images yet"; line: "Scout looks for the bot's Images on screen. Take some first."
            action: "Capture"; actionIcon: "▣"; keyName: "capture.freeze"
            onActed: studio.openCapture("any")
        }
    }
    // what a list with nothing in it says: no Images at all, or none in the group picked
    function emptyText() {
        if (scout.total === 0)
            return { glyph: "◎", title: "No Images yet", line: "Scout looks for the bot's Images on screen. Take some first.", action: "Capture" }
        if (scout.group === "weak") return { glyph: "✓", title: "Nothing weak", line: "Every Image seen is found as well as it needs." }
        if (scout.group === "not") return { glyph: "✓", title: "Every Image has been seen", line: "" }
        return { glyph: "◎", title: "Nothing seen yet", line: "Go through the game's screens: each Image found is ticked off here." }
    }
    Timer { interval: 1000; repeat: true; running: scoutPill.visible; onTriggered: scoutPill.now = Date.now() / 1000 }

    // ---- docked on the top or bottom: the row
    Ring {
        visible: !scoutPill.column
        width: 30; height: 30; thickness: 3; small: true; tokens: studio.pillMotion
        done: scout.seen; total: Math.max(1, scout.total)
        Layout.leftMargin: 2
    }
    Text {
        visible: !scoutPill.column
        objectName: "scoutSeen"
        text: scoutPill.seen
        color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
    }
    Chip { visible: !scoutPill.column && scout.weak > 0; height: 22; tone: "warn"; text: scout.weak + " weak" }
    Chip { visible: !scoutPill.column && scout.notSeen > 0; height: 22; text: scout.notSeen + " not yet" }
    Text { visible: !scoutPill.column; text: "· " + scoutPill.took; color: studio.colors.muted; font.pixelSize: 13 }
    Rectangle { visible: scoutPill.row; Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
    Segmented {
        objectName: "scoutGroups"
        tokens: studio.pillMotion
        visible: scoutPill.row
        strong: true; itemHeight: 30
        current: scout.group
        model: scoutPill.groups
        onPicked: function (key) { scout.setGroup(key) }
    }
    PillAction { visible: scoutPill.row; glyph: "‹"; tip: "The image before (" + scoutPill.key("scout.previous") + ")"; onClicked: scout.previous() }
    Chip { visible: scoutPill.row && scoutPill.key("scout.next") !== ""; height: 22; tone: "info"; text: scoutPill.key("scout.next") }
    PillAction { visible: scoutPill.row; glyph: "›"; tip: "The next image (" + scoutPill.key("scout.next") + ")"; onClicked: scout.next() }

    // ---- docked on a side: the column, with the groups in a list
    Column {
        id: side
        visible: scoutPill.column
        Layout.preferredWidth: 372
        spacing: 8
        RowLayout {
            width: parent.width; spacing: 10
            Ring { width: 44; height: 44; thickness: 4; small: true; tokens: studio.pillMotion; done: scout.seen; total: Math.max(1, scout.total) }
            Column {
                Layout.fillWidth: true
                Text { text: scoutPill.seen; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold }
                Text { text: "a pass every 0.5 s · " + scoutPill.took; color: studio.colors.muted; font.pixelSize: 12 }
            }
            PillAction { glyph: "✕"; tip: "Hide Scout"; onClicked: scout.stop() }
            PillAction { glyph: "⤢"; tip: "Open darbit Studio"; onClicked: studio.toggleScout() }
        }
        Rectangle { width: parent.width; height: 1; color: studio.colors.line }
        Loader {
            width: parent.width
            active: scout.total === 0 && scoutPill.column && scoutPill.visible  // made only when shown
            visible: active
            sourceComponent: noImages
        }
        ListView {
            id: lines
            objectName: "scoutLines"
            width: parent.width
            height: Math.min(contentHeight, 520)
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            SmoothWheel { view: lines }
            readonly property var order: ({ "not": 0, "weak": 1, "seen": 2 })
            model: scout.images
                .filter(function (image) { return !scoutPill.folded[image.state] })
                .concat(["not", "weak", "seen"].filter(function (state) { return scoutPill.folded[state] }).map(function (state) { return { state: state, folded: true } }))
                .sort(function (a, b) { return lines.order[a.state] - lines.order[b.state] })
            section.property: "state"
            section.delegate: Item {
                required property string section
                width: lines.width; height: 30
                readonly property int count: section === "not" ? scout.notSeen : section === "weak" ? scout.weak : scout.seen
                Row {
                    x: 8; anchors.verticalCenter: parent.verticalCenter; spacing: 8
                    Text { text: scoutPill.folded[parent.parent.section] ? "▸" : "▾"; color: studio.colors.faint; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                    Text {
                        text: Scout.groupLabel(parent.parent.section).toUpperCase()
                        color: studio.colors.muted; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.2
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Chip {
                        height: 18; anchors.verticalCenter: parent.verticalCenter
                        tone: parent.parent.section === "weak" ? "warn" : parent.parent.section === "seen" ? "ok" : "plain"
                        text: parent.parent.count
                    }
                }
                MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        var next = Object.assign({}, scoutPill.folded)
                        next[parent.section] = !next[parent.section]
                        scoutPill.folded = next
                    }
                }
            }
            delegate: Loader {
                required property var modelData
                width: lines.width
                height: modelData.folded ? 0 : item ? item.height : 0
                active: !modelData.folded
                sourceComponent: ScoutLine {
                    width: lines.width
                    image: modelData
                    on: modelData.name === scout.landed
                    onPicked: scout.landOn(modelData.name)
                    onRetakeOnShot: scoutPill.retakeOnShot(modelData)
                    onRetakeNow: scoutPill.retakeNow(modelData)
                }
            }
        }
        Rectangle { width: parent.width; height: 1; color: studio.colors.line }
        RowLayout {
            width: parent.width
            Text { text: "Hover a line for its retakes"; color: studio.colors.faint; font.pixelSize: 12; Layout.fillWidth: true; Layout.leftMargin: 6 }
            PillButton { small: true; kind: "quiet"; text: "Reset the session"; onClicked: scout.reset() }
        }
    }
    Rectangle { visible: scoutPill.row; Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
    PillAction { visible: !scoutPill.column; glyph: "✕"; label: "Hide"; tip: scoutPill.key("scout.toggle") ? "Hide Scout (" + scoutPill.key("scout.toggle") + ")" : "Hide Scout"; onClicked: scout.stop() }
    PillAction { visible: !scoutPill.column; glyph: "⤢"; label: "Studio"; tip: "Open darbit Studio"; onClicked: studio.toggleScout() }

    // ---- docked on the top or bottom: the strip of the group's images and the one landed on
    below: Rectangle {
        id: strip
        objectName: "scoutStrip"
        visible: scoutPill.row
        width: parent.width
        height: stripColumn.implicitHeight + 20
        radius: 18
        color: studio.colors.solid
        border.color: studio.colors.line
        Column {
            id: stripColumn
            x: 10; y: 10; width: parent.width - 20
            spacing: 10
            ListView {
                id: tiles
                objectName: "scoutTiles"
                visible: count > 0
                width: parent.width; height: 100
                orientation: ListView.Horizontal
                spacing: 6; clip: true
                boundsBehavior: Flickable.StopAtBounds
                SmoothWheel { view: tiles; sideways: true }
                model: scout.listed
                currentIndex: {
                    for (var index = 0; index < scout.listed.length; index++)
                        if (scout.listed[index].name === scout.landed) return index
                    return -1
                }
                onCurrentIndexChanged: if (currentIndex >= 0) positionViewAtIndex(currentIndex, ListView.Contain)
                highlightFollowsCurrentItem: false
                delegate: ScoutTile {
                    required property var modelData
                    image: modelData
                    on: modelData.name === scout.landed
                    onPicked: scout.landOn(modelData.name)
                }
            }
            Item {
                visible: tiles.count === 0
                width: parent.width; height: stripEmpty.height + 16
                Loader {
                    id: stripEmpty
                    width: parent.width
                    anchors.centerIn: parent
                    active: tiles.count === 0 && scoutPill.row && scoutPill.visible  // made only when shown
                    sourceComponent: EmptyState {
                        objectName: "scoutEmpty"
                        compact: true; tokens: studio.pillMotion
                        readonly property var says: scoutPill.emptyText()
                        glyph: says.glyph; title: says.title; line: says.line
                        action: says.action || ""; actionIcon: "▣"; keyName: says.action ? "capture.freeze" : ""
                        onActed: studio.openCapture("any")
                    }
                }
            }
            Rectangle { visible: scoutPill.landedImage !== null; width: parent.width; height: 1; color: studio.colors.line }
            // the one landed on: what it is, what's wrong, and its retakes
            RowLayout {
                visible: scoutPill.landedImage !== null
                width: parent.width; spacing: 10
                Rectangle {
                    Layout.preferredWidth: 40; Layout.preferredHeight: 28; radius: 6
                    color: studio.colors.bg
                    border.color: Scout.ink(studio.colors, scoutPill.landedImage); border.width: 2
                    clip: true
                    Thumbnail {
                        anchors.fill: parent; anchors.margins: 2
                        source: scoutPill.landedImage ? scoutPill.landedImage.file : ""
                    }
                }
                Column {
                    Text {
                        width: Math.min(implicitWidth, 300)
                        elide: Text.ElideRight
                        text: scoutPill.landedImage ? scoutPill.landedImage.name : ""
                        color: studio.colors.text; font.family: "monospace"; font.pixelSize: 12; font.weight: Font.Bold
                        // a name too long for the strip: whole on hover
                        HoverHandler { id: landedHover }
                        ToolTip.visible: landedHover.hovered && truncated
                        ToolTip.text: text
                        ToolTip.delay: 400
                    }
                    Text {
                        objectName: "scoutLandedLine"
                        text: "Image · " + Scout.seenLine(scoutPill.landedImage, scoutPill.now, scoutPill.landedHere)
                        color: studio.colors.muted; font.pixelSize: 12
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: Scout.problem(scoutPill.landedImage)
                    elide: Text.ElideRight
                    color: scoutPill.landedImage && scoutPill.landedImage.state === "not" ? studio.colors.muted : studio.colors.warn
                    font.pixelSize: 12
                }
                PillButton {
                    objectName: "stripRetakeOnShot"
                    visible: !!scoutPill.landedImage && scoutPill.landedImage.shot !== ""
                    kind: "primary"; small: true; icon: "⟲"
                    text: scoutPill.landedImage ? "Retake on " + scoutPill.landedImage.seenOn + ", where it was seen" : ""
                    onClicked: scoutPill.retakeOnShot(scoutPill.landedImage)
                }
                PillButton {
                    objectName: "stripRetakeNow"
                    small: true; icon: "⟲"; text: "On the screen now"
                    kind: scoutPill.landedImage && scoutPill.landedImage.shot !== "" ? "plain" : "primary"
                    onClicked: scoutPill.retakeNow(scoutPill.landedImage)
                }
            }
        }
    }

    // ---- floating: every image in a grid; one clicked, in full
    heading: [
        Ring { width: 30; height: 30; thickness: 3; small: true; tokens: studio.pillMotion; done: scout.seen; total: Math.max(1, scout.total) },
        Text { text: scoutPill.seen; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold },
        Chip { visible: scout.weak > 0; height: 22; tone: "warn"; text: scout.weak + " weak" },
        Chip { visible: scout.notSeen > 0; height: 22; text: scout.notSeen + " not yet" },
        Item { Layout.fillWidth: true }
    ]
    card: [
        Loader {
            width: parent.width
            active: !scoutPill.opened && scout.total === 0 && scoutPill.form === "card" && scoutPill.visible
            visible: active
            sourceComponent: noImages
        },
        Item {
            objectName: "scoutGrid"
            visible: !scoutPill.opened
            width: parent.width
            height: Math.min(grid.contentHeight, 300)
            GridView {
                id: grid
                anchors.fill: parent
                cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 60))); cellHeight: 50
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                SmoothWheel { view: grid }
                model: scout.images
                delegate: Item {
                    required property var modelData
                    width: grid.cellWidth; height: grid.cellHeight
                    ScoutTile {
                        anchors.centerIn: parent
                        compact: true
                        image: parent.modelData
                        on: parent.modelData.name === scout.landed
                        onPicked: scoutPill.open(parent.modelData.name)
                    }
                }
            }
        },
        RowLayout {
            visible: !scoutPill.opened
            width: parent.width; spacing: 12
            Row { spacing: 6; Rectangle { width: 10; height: 10; radius: 3; color: studio.colors.ok; anchors.verticalCenter: parent.verticalCenter }
                  Text { text: scout.seen + " seen"; color: studio.colors.muted; font.pixelSize: 12 } }
            Row { spacing: 6; Rectangle { width: 10; height: 10; radius: 3; color: studio.colors.warn; anchors.verticalCenter: parent.verticalCenter }
                  Text { text: scout.weak + " weak"; color: studio.colors.muted; font.pixelSize: 12 } }
            Row { spacing: 6; Rectangle { width: 10; height: 10; radius: 3; color: "transparent"; border.color: studio.colors.faint; anchors.verticalCenter: parent.verticalCenter }
                  Text { text: scout.notSeen + " not seen yet"; color: studio.colors.muted; font.pixelSize: 12 } }
            Item { Layout.fillWidth: true }
            Text { text: "Click one for its detail"; color: studio.colors.faint; font.pixelSize: 12 }
        },
        RowLayout {
            visible: scoutPill.opened
            width: parent.width; spacing: 6
            PillButton { objectName: "scoutBack"; small: true; kind: "quiet"; icon: "‹"; text: "Every image"; onClicked: scoutPill.opened = false }
            Item { Layout.fillWidth: true }
            PillAction { glyph: "‹"; tip: "The image before (" + scoutPill.key("scout.previous") + ")"; onClicked: scout.previous() }
            Text {
                text: {
                    for (var index = 0; index < scout.listed.length; index++)
                        if (scout.listed[index].name === scout.landed) return (index + 1) + " of " + scout.listed.length
                    return ""
                }
                color: studio.colors.muted; font.pixelSize: 12
            }
            PillAction { glyph: "›"; tip: "The next image (" + scoutPill.key("scout.next") + ")"; onClicked: scout.next() }
        },
        ScoutDetail {
            objectName: "scoutDetail"
            visible: scoutPill.opened && scoutPill.landedImage !== null
            width: parent.width
            image: scoutPill.landedImage
            now: scoutPill.now
            here: scoutPill.landedHere
            onRetakeOnShot: scoutPill.retakeOnShot(scoutPill.landedImage)
            onRetakeNow: scoutPill.retakeNow(scoutPill.landedImage)
        },
        RowLayout {
            width: parent.width; spacing: 8
            PillButton { small: true; icon: "✕"; text: "Hide"; onClicked: scout.stop() }
            PillButton { small: true; kind: "quiet"; text: "Reset the session"; onClicked: scout.reset() }
            Item { Layout.fillWidth: true }
            PillButton { small: true; icon: "⤢"; text: "Open Studio"; onClicked: studio.toggleScout() }
        }
    ]
}
