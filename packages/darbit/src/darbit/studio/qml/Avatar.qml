// A bot's square: its accent (or darbit's) with its initials.
import QtQuick
import "format.js" as Format

Rectangle {
    property string name: ""
    property string accent: ""
    property int size: 32
    width: size; height: size; radius: size * 0.3
    color: accent !== "" ? accent : studio.colors.accent2
    Text {
        anchors.centerIn: parent
        text: Format.initials(parent.name)
        color: "#1a0b14"
        font.pixelSize: parent.size * 0.4; font.weight: Font.Bold
    }
}
