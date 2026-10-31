// A rounded bar that holds buttons: the bot picker, the page tabs, the run controls.
import QtQuick

Rectangle {
    default property alias items: row.data
    property int spacing: 4
    height: 52
    width: row.implicitWidth + 12
    radius: height / 2
    color: studio.colors.glass
    border.color: studio.colors.line
    border.width: 1

    Row {
        id: row
        anchors.verticalCenter: parent.verticalCenter
        x: 6
        spacing: parent.spacing
    }
}
