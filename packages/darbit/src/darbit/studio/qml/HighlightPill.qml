// Highlight's pill: the shared pill at the top of the screen while Highlight is on, like the run pill. What's found,
// how long a pass takes, look-alikes as a warning, then Hide (back to the game) and ⤢ (back to the Studio). It slides
// out of sight a few seconds after the mouse leaves it; the mouse at the top edge brings it back. The boxes on the game
// (HighlightWindow) still let every click through.
import QtQuick
import QtQuick.Layouts

PillWindow {
    id: highlightPill
    hiding: highlightHiding
    title: "darbit Highlight pill"

    Row {
        Layout.leftMargin: 12; Layout.rightMargin: 6
        spacing: 9
        Rectangle { width: 11; height: 11; radius: 5.5; color: studio.colors.ok; anchors.verticalCenter: parent.verticalCenter }
        Text {
            text: "Highlight"
            color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            objectName: "highlightFound"
            text: highlight.found + " of " + highlight.boxes.length + " found · " + Math.round(highlight.took) + " ms"
            color: studio.colors.muted; font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            visible: highlight.alike > 0
            text: "⚠ " + highlight.alike + (highlight.alike === 1 ? " look-alike" : " look-alikes")
            color: studio.colors.warn; font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Rectangle { Layout.preferredWidth: 1; Layout.preferredHeight: 24; color: studio.colors.line }
    IconButton { glyph: "✕"; tip: "Hide Highlight (Ctrl+Alt+H)"; onClicked: highlight.stop() }
    IconButton { glyph: "⤢"; tip: "Open darbit Studio"; onClicked: studio.toggleHighlight() }
}
