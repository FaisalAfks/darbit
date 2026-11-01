// The ghost cursor (#117): a ripple where the bot clicks and the keys it presses, over the game, for a moment each.
// Clicks go through to the game, and it never takes the focus. It shows only while there's a mark to show.
import QtQuick
import QtQuick.Window

Window {
    id: ghostWindow
    // only around its marks: a window the size of the screen redrew every pixel each frame while a bot pressed keys
    // (shown and hidden as it is: FullScreen would ask for the focus every time)
    visible: studio.ghost && ghost.marks.length > 0
    readonly property rect area: around(ghost.marks)
    x: area.x; y: area.y; width: area.width; height: area.height
    transientParent: null  // its own window: it shows while the Studio is hidden or minimised
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus | Qt.Tool
    color: "transparent"
    title: "darbit ghost cursor"
    Component.onCompleted: ghost.keepOutOfCaptures(ghostWindow)
    readonly property real ratio: Screen.devicePixelRatio  // marks come in screen pixels
    readonly property var keys: ghost.marks.filter(function (mark) { return mark.kind === "key" })
    function place(value, origin) { return value / ratio - origin }
    // the marks' room: a ring and its button name around a click, the keycaps (at most 6) right of a key
    function around(marks) {
        var left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity
        for (var i = 0; i < marks.length; i++) {
            var x = marks[i].x / ratio, y = marks[i].y / ratio
            left = Math.min(left, x - 40); top = Math.min(top, y - 40)
            right = Math.max(right, x + (marks[i].kind === "key" ? 480 : 160)); bottom = Math.max(bottom, y + 70)
        }
        if (right < left)
            return Qt.rect(Screen.virtualX, Screen.virtualY, 1, 1)
        return Qt.rect(Math.floor(left), Math.floor(top), Math.ceil(right - left), Math.ceil(bottom - top))
    }

    // a click: a ring that opens and fades, and a dot where it landed
    Repeater {
        model: ghost.marks.filter(function (mark) { return mark.kind === "click" })
        delegate: Item {
            required property var modelData
            x: ghostWindow.place(modelData.x, ghostWindow.x); y: ghostWindow.place(modelData.y, ghostWindow.y)
            Rectangle {
                id: ring
                width: 44; height: 44; radius: 22
                x: -width / 2; y: -height / 2
                color: "transparent"
                border.width: 3; border.color: studio.colors.accent
                transformOrigin: Item.Center
                NumberAnimation on scale { from: 0.3; to: 1.2; duration: studio.effects ? 650 : 0; easing.type: Easing.OutCubic }
                NumberAnimation on opacity { from: 1; to: 0; duration: studio.effects ? 850 : 0; easing.type: Easing.InQuad }
            }
            Rectangle {
                width: 10; height: 10; radius: 5; x: -5; y: -5
                color: studio.colors.accent; border.width: 2; border.color: "white"
            }
            Rectangle {
                visible: modelData.name !== "left"
                x: 14; y: 10; radius: 8
                width: buttonName.implicitWidth + 12; height: buttonName.implicitHeight + 4
                color: studio.colors.glassStrong
                Text { id: buttonName; anchors.centerIn: parent; text: modelData.name; color: studio.colors.text; font.pixelSize: 11 }
            }
        }
    }

    // keys: keycaps beside the cursor, the newest last
    Row {
        visible: ghostWindow.keys.length > 0
        readonly property var last: ghostWindow.keys.length ? ghostWindow.keys[ghostWindow.keys.length - 1] : null
        x: last ? ghostWindow.place(last.x, ghostWindow.x) + 18 : 0
        y: last ? ghostWindow.place(last.y, ghostWindow.y) + 20 : 0
        spacing: 5
        Repeater {
            model: ghostWindow.keys.slice(-6)
            delegate: Rectangle {
                required property var modelData
                width: Math.max(30, cap.implicitWidth + 16); height: 30; radius: 8
                color: studio.colors.glassStrong
                border.width: 1; border.color: studio.colors.accent
                Text {
                    id: cap
                    anchors.centerIn: parent
                    text: modelData.name.length === 1 ? modelData.name.toUpperCase() : modelData.name
                    color: studio.colors.text; font.pixelSize: 13; font.weight: Font.DemiBold
                }
                NumberAnimation on opacity { from: 1; to: 0.15; duration: studio.effects ? 900 : 0; easing.type: Easing.InQuad }
            }
        }
    }
}
