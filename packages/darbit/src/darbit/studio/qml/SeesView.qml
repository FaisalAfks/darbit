// What the bot sees (#316): the screen at the bot's last look, with what it looked for boxed (found: solid in the
// accent with its name and score; not found: dashed red at its closest spot), and the look under it. It follows the
// bot's look file only while it's in sight (studio/sees.py): on another page, or with the window hidden or minimized,
// nothing is read and the frame stays as it was.
import QtQuick
import QtQuick.Shapes

Column {
    id: seen
    property var info: ({})  // the block's data: {look, logs} (server/overview.py)
    readonly property var frame: sees.frame || ({})
    readonly property bool has: !!frame.file
    readonly property bool inSight: visible && studio.shown
    width: parent ? parent.width : 0
    spacing: 12

    function follow() { sees.follow(inSight && info && info.look ? info.look : "", info && info.logs ? info.logs : "") }
    function named(name) { return String(name).replace(/\.png$/i, "") }
    onInSightChanged: follow()
    onInfoChanged: follow()
    Component.onCompleted: follow()
    Component.onDestruction: sees.follow("", "")

    // a dashed box, for a target that wasn't found (as Scout draws regions)
    component Dashed: Shape {
        id: dashed
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: studio.colors.danger; strokeWidth: 2; fillColor: "transparent"
            strokeStyle: ShapePath.DashLine; dashPattern: [4, 3]
            startX: 0; startY: 0
            PathLine { x: dashed.width; y: 0 }
            PathLine { x: dashed.width; y: dashed.height }
            PathLine { x: 0; y: dashed.height }
            PathLine { x: 0; y: 0 }
        }
    }

    Rectangle {
        width: parent.width; height: Math.round(width * 9 / 16)
        radius: 10; color: studio.colors.bg; clip: true
        Image {
            id: shot
            anchors.fill: parent
            source: seen.has ? seen.frame.file : ""
            fillMode: Image.PreserveAspectFit
            cache: false
            asynchronous: false  // a small JPEG: loaded at once, the last one stays until the new one is in
        }
        Item {  // the frame as drawn, its boxes on it
            x: (parent.width - shot.paintedWidth) / 2; y: (parent.height - shot.paintedHeight) / 2
            width: shot.paintedWidth; height: shot.paintedHeight
            readonly property real fit: seen.frame.w ? width / seen.frame.w : 1
            Repeater {
                model: seen.frame.boxes || []
                delegate: Item {
                    id: box
                    required property var modelData
                    x: modelData.x * parent.fit; y: modelData.y * parent.fit
                    width: Math.max(6, modelData.w * parent.fit); height: Math.max(6, modelData.h * parent.fit)
                    Rectangle {
                        visible: box.modelData.found
                        anchors.fill: parent
                        color: "transparent"; radius: 2
                        border.color: studio.colors.accent; border.width: 2
                    }
                    Dashed { visible: !box.modelData.found; anchors.fill: parent }
                    Rectangle {  // the found one's name and score
                        visible: box.modelData.found
                        x: 0; y: box.y >= height + 2 ? -height - 2 : 2
                        width: label.implicitWidth + 12; height: 18; radius: 4
                        color: studio.colors.accent
                        Text {
                            id: label
                            anchors.centerIn: parent
                            text: seen.named(box.modelData.name) + " " + Number(box.modelData.score).toFixed(2)
                            color: studio.colors.onAccent; font.pixelSize: 11; font.weight: Font.DemiBold
                        }
                    }
                }
            }
        }
        Text { visible: !seen.has; anchors.centerIn: parent; text: "Nothing seen yet"; color: studio.colors.faint; font.pixelSize: 13 }
    }
    Row {
        visible: seen.has
        width: parent.width; spacing: 10
        Text { id: kindText; text: seen.frame.kind || ""; color: studio.colors.text; font.pixelSize: 12; font.weight: Font.DemiBold }
        Text {
            width: parent.width - kindText.width - parent.spacing; elide: Text.ElideRight
            text: (seen.frame.targets || []).map(seen.named).join(", ")
                + (seen.frame.found ? " → found " + seen.named(seen.frame.found) : " → not found")
            color: studio.colors.muted; font.pixelSize: 12
        }
    }
}
