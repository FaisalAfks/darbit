// The pill every darbit tool floats over the game: Capture's, the recorder's and the run pill. One shape and one solid
// colour (no see-through glass over a game), so the three never drift apart. Put its controls inside, left to right;
// where it sits and how it hides is up to its window.
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: pill
    default property alias content: row.data
    property color edge: studio.colors.line  // the border: a state's colour (recording, paused) or the plain line
    // the panel colour, made solid
    readonly property color solid: Qt.rgba(studio.colors.glassStrong.r, studio.colors.glassStrong.g, studio.colors.glassStrong.b, 1)
    width: row.implicitWidth + 16
    height: 56
    radius: 28
    color: solid
    border.color: edge
    border.width: 1
    Behavior on width { NumberAnimation { duration: studio.effects ? 180 : 0; easing.type: Easing.OutCubic } }
    RowLayout {
        id: row
        anchors { left: parent.left; leftMargin: 8; verticalCenter: parent.verticalCenter }
        spacing: 6
    }
}
