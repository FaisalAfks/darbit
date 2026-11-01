// A row of choices in a pill, with one highlight that glides to the chosen one.
// model: [{ key, label, icon?, count?, tone? }]; `current` is the chosen key.
import QtQuick

Rectangle {
    id: seg
    property var model: []
    property string current: ""
    property int itemHeight: 36
    property bool strong: true  // the accent highlight; off: a quieter raised one
    signal picked(string key)
    readonly property int speed: studio.effects ? 220 : 0

    implicitWidth: row.implicitWidth + 8
    implicitHeight: itemHeight + 8
    radius: height / 2
    color: studio.colors.glass
    border.color: studio.colors.line

    Rectangle {
        id: glide
        readonly property Item target: row.children.length > 0 ? row.chosen() : null
        x: target ? target.x + 4 : 4
        y: 4
        width: target ? target.width : 0
        height: seg.itemHeight
        radius: height / 2
        visible: target !== null
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: seg.strong ? studio.colors.accent : studio.colors.raisedHover }
            GradientStop { position: 1; color: seg.strong ? Qt.tint(studio.colors.accent, Qt.rgba(0.65, 0.55, 0.98, 0.35)) : studio.colors.raisedHover }
        }
        Behavior on x { NumberAnimation { duration: seg.speed; easing.type: Easing.OutCubic } }
        Behavior on width { NumberAnimation { duration: seg.speed; easing.type: Easing.OutCubic } }
    }

    Row {
        id: row
        x: 4; y: 4
        function chosen() {
            for (var index = 0; index < children.length; index++)
                if (children[index].key === seg.current) return children[index]
            return null
        }
        Repeater {
            model: seg.model
            delegate: Item {
                id: item
                required property var modelData
                readonly property string key: modelData.key
                readonly property bool on: key === seg.current
                width: label.implicitWidth + 30
                height: seg.itemHeight
                Row {
                    id: label
                    anchors.centerIn: parent
                    spacing: 7
                    Text {
                        visible: !!item.modelData.icon
                        text: item.modelData.icon || ""
                        color: item.on && seg.strong ? studio.colors.onAccent : studio.colors.muted
                        font.pixelSize: 13; font.family: studio.symbols
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: item.modelData.label
                        color: item.on && seg.strong ? studio.colors.onAccent
                            : item.modelData.tone === "danger" ? studio.colors.danger
                            : item.modelData.tone === "warn" ? studio.colors.warn
                            : item.on ? studio.colors.text : hover.containsMouse ? studio.colors.text : studio.colors.muted
                        font.pixelSize: 14; font.weight: Font.DemiBold
                        anchors.verticalCenter: parent.verticalCenter
                        Behavior on color { ColorAnimation { duration: seg.speed / 2 } }
                    }
                    Text {
                        visible: item.modelData.count !== undefined
                        text: item.modelData.count !== undefined ? item.modelData.count : ""
                        color: item.on && seg.strong ? studio.colors.onAccent : studio.colors.faint
                        font.pixelSize: 12; font.weight: Font.DemiBold
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                MouseArea {
                    id: hover
                    anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                    onClicked: seg.picked(item.key)
                }
            }
        }
    }
}
