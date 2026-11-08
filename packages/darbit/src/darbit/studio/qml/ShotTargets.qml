// The targets taken on one frozen shot, as tiles in Capture's pill: each one's image (cut from the shot), its name,
// its kind and, after Test, what was found. A click makes one the active one, ✕ drops it. One row that scrolls
// sideways in a pill on the top or bottom edge; two columns that scroll up and down on a side or floating (`vertical`).
// entries: Capture's `shown` ({ index, name, kind, box, image, region, location, scoreText, scoreShort, scoreTone }).
// The view's model is only their count, so a box nudged or renamed updates its tile in place and the scroll stays.
import QtQuick

GridView {
    id: tiles
    property var entries: []
    property bool vertical: false
    property int active: -1
    property string source: ""  // the shot's image://capture/… address: a tile asks for its part of it
    property int rows: 3        // how many rows show at once in the column form
    signal picked(int index)
    signal removed(int index)

    readonly property int tileWidth: vertical ? Math.floor(width / 2) - 4 : 150
    readonly property int tileHeight: vertical ? 104 : 116
    cellWidth: tileWidth + (vertical ? 4 : 8)
    cellHeight: tileHeight + (vertical ? 6 : 0)
    flow: vertical ? GridView.FlowLeftToRight : GridView.FlowTopToBottom
    flickableDirection: vertical ? Flickable.VerticalFlick : Flickable.HorizontalFlick
    implicitHeight: vertical ? Math.min(Math.ceil(count / 2), rows) * cellHeight : tileHeight
    boundsBehavior: Flickable.StopAtBounds
    clip: true
    model: entries.length
    readonly property var empty: ({ index: -1, name: "", kind: "image", box: [0, 0, 1, 1], scoreText: "", scoreShort: "", scoreTone: "plain" })
    // the active one stays in sight as N steps through them
    onActiveChanged: { if (vertical) console.warn("DBG activeChanged", active, "cy", contentY, "count", count, "len", entries.length, "vis", visible); Qt.callLater(showActive) }
    onContentYChanged: if (vertical) console.warn("DBG cy ->", contentY, "h", height, "ch", contentHeight, "count", count)
    onHeightChanged: if (vertical) console.warn("DBG h ->", height)
    onCountChanged: if (vertical) console.warn("DBG count ->", count)
    function showActive() {
        if (vertical) console.warn("DBG showActive active", active, "cy", contentY, "h", height, "ch", contentHeight, "count", count, "len", entries.length, "vis", visible, "idx", JSON.stringify(entries.map(function (e) { return e.index })))
        forceLayout()
        for (var at = 0; at < entries.length; at++) {
            if (entries[at].index === active) { positionViewAtIndex(at, GridView.Contain); break }
        }
        if (vertical) console.warn("DBG after showActive cy", contentY)
    }
    Component.onCompleted: console.warn("DBG completed", objectName, vertical)
    SmoothWheel { view: tiles; sideways: !tiles.vertical }

    function inkOf(kind) { return kind === "region" ? studio.colors.kindRegion : kind === "location" ? studio.colors.kindLocation : studio.colors.kindImage }
    // the part of the shot a tile shows: its box, or around its location
    function partOf(entry) {
        var box = entry.location && !entry.image && !entry.region ? [entry.location[0] - 32, entry.location[1] - 32, 64, 64] : entry.box
        return tiles.source + "/" + box.map(Math.round).join(",")
    }

    delegate: Rectangle {
        id: tile
        required property int index
        readonly property var entry: tiles.entries[index] || tiles.empty
        readonly property bool on: entry.index === tiles.active
        readonly property color ink: tiles.inkOf(entry.kind)
        width: tiles.tileWidth; height: tiles.tileHeight
        radius: 12
        color: on ? Qt.rgba(ink.r, ink.g, ink.b, 0.12) : area.containsMouse ? studio.colors.raisedHover : studio.colors.raised
        border.color: on ? ink : studio.colors.line
        border.width: on ? 2 : 1
        Behavior on color { ColorAnimation { duration: studio.effects ? 120 : 0 } }
        MouseArea {
            id: area
            anchors.fill: parent; hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: tiles.picked(tile.entry.index)
        }
        Rectangle {  // its image, cut from the shot
            id: thumb
            x: 6; y: 6; width: parent.width - 12; height: tiles.vertical ? 46 : 58
            radius: 8; clip: true
            color: "black"; border.color: Qt.rgba(tile.ink.r, tile.ink.g, tile.ink.b, 0.7)
            Image {
                anchors.fill: parent; anchors.margins: 1
                source: tiles.source ? tiles.partOf(tile.entry) : ""
                fillMode: Image.PreserveAspectCrop
                smooth: true; asynchronous: false
            }
            Item {  // a location: its crosshair in the middle
                visible: tile.entry.kind === "location"
                anchors.centerIn: parent
                Rectangle { x: -1; y: -8; width: 2; height: 16; color: tile.ink }
                Rectangle { x: -8; y: -1; width: 16; height: 2; color: tile.ink }
            }
            Rectangle {  // ✕: drop it from the shot
                objectName: "dropTile"
                anchors { right: parent.right; top: parent.top; margins: 4 }
                width: 20; height: 20; radius: 10
                visible: area.containsMouse || drop.containsMouse || tile.on
                color: drop.containsMouse ? studio.colors.danger : studio.colors.solid
                border.color: studio.colors.line
                Text { anchors.centerIn: parent; text: "✕"; color: drop.containsMouse ? studio.colors.onStatus : studio.colors.text; font.pixelSize: 10; font.family: studio.symbols }
                MouseArea { id: drop; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: tiles.removed(tile.entry.index) }
            }
        }
        Text {
            id: nameLine
            x: 8; y: thumb.y + thumb.height + 5; width: parent.width - 16
            text: tile.entry.name
            elide: Text.ElideLeft  // a time-stamp name: its last digits tell it apart
            color: studio.colors.text; font.family: "monospace"; font.pixelSize: 11
        }
        Row {
            x: 8; y: nameLine.y + nameLine.height + 5
            spacing: 5
            // its kind: a word in the row form, a dot of its colour in the narrow column
            Chip {
                visible: !tiles.vertical
                height: 20
                tone: "plain"
                text: tile.entry.kind.charAt(0).toUpperCase() + tile.entry.kind.slice(1)
                border.color: Qt.rgba(tile.ink.r, tile.ink.g, tile.ink.b, 0.6)
            }
            Rectangle { visible: tiles.vertical; width: 8; height: 8; radius: 2; color: tile.ink; anchors.verticalCenter: parent.verticalCenter }
            Chip {
                visible: tile.entry.scoreText !== ""
                height: 20
                tone: tile.entry.scoreTone
                text: tiles.vertical ? tile.entry.scoreShort : tile.entry.scoreText
            }
        }
    }
}
