// The run control: Play while stopped; while running, the state and its time with Pause and Stop. It changes shape
// between the two instead of showing buttons that can't be used.
import QtQuick
import "format.js" as Format

Rectangle {
    id: control
    readonly property string state: studio.bot.status || "stopped"
    readonly property bool active: state === "running" || state === "paused"
    readonly property color dot: state === "running" ? studio.colors.ok : state === "paused" ? studio.colors.warn
        : state === "failed" ? studio.colors.danger : studio.colors.faint
    height: 48
    width: row.implicitWidth + 12
    radius: 24
    color: studio.colors.glass
    border.color: studio.colors.line
    clip: true
    Behavior on width { NumberAnimation { duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic } }

    Row {
        id: row
        x: 6; anchors.verticalCenter: parent.verticalCenter
        spacing: 4
        Item {
            width: label.implicitWidth + 26; height: 36
            Row {
                id: label
                x: 12; anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                Rectangle {
                    width: 9; height: 9; radius: 4.5; color: control.dot
                    anchors.verticalCenter: parent.verticalCenter
                    // a soft halo while running: drawn once, not animated, so an idle Studio doesn't redraw
                    Rectangle {
                        visible: control.state === "running"
                        anchors.centerIn: parent; width: 19; height: 19; radius: 9.5
                        color: Qt.rgba(control.dot.r, control.dot.g, control.dot.b, 0.22)
                        z: -1
                    }
                }
                Text {
                    text: control.state.charAt(0).toUpperCase() + control.state.slice(1)
                    color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    visible: control.active && !!studio.bot.since
                    text: Format.duration(studio.now - (studio.bot.since || studio.now))
                    color: studio.colors.muted; font.pixelSize: 14
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
        PillButton {
            visible: !control.active
            kind: "primary"; icon: "▶"; text: "Play"; small: true
            anchors.verticalCenter: parent.verticalCenter
            onClicked: studio.start()
        }
        PillButton {
            visible: control.active
            kind: "quiet"; icon: control.state === "paused" ? "▶" : "❚❚"; small: true
            text: control.state === "paused" ? "Go on" : ""
            anchors.verticalCenter: parent.verticalCenter
            onClicked: studio.pause()
        }
        PillButton {
            visible: control.active
            kind: "quiet"; icon: "■"; small: true
            anchors.verticalCenter: parent.verticalCenter
            onClicked: studio.stop()
        }
    }
}
