// The pill every darbit tool floats over the game: Capture's, the recorder's, Highlight's and the run pill. One shape
// and one solid colour (no see-through glass over a game), so they never drift apart. Put its controls inside, in
// order: a row on the top and bottom edges, a column on the sides (`vertical`), where they show their labels. The grip
// at its start is where it's dragged from; PillBody places it and moves it.
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: pill
    default property alias content: grid.data
    property color ink: studio.colors.line  // the border: a state's colour (recording, paused) or the plain line
    property bool vertical: false
    property bool bare: false  // inside a floating card: no fill or border of its own, and no grip
    property bool movable: false  // a pill over the game (PillBody): its grip shows
    // the panel colour, made solid
    readonly property color solid: studio.colors.solid
    width: grid.implicitWidth + (vertical ? 20 : 16)
    height: vertical ? grid.implicitHeight + 20 : 56
    radius: vertical ? 22 : 28
    color: bare ? "transparent" : solid
    border.color: ink
    border.width: bare ? 0 : 1
    Behavior on width { enabled: !pill.vertical; NumberAnimation { duration: studio.effects ? 180 : 0; easing.type: Easing.OutCubic } }
    GridLayout {
        id: grid
        x: pill.vertical ? 10 : 8
        y: pill.vertical ? 10 : (pill.height - height) / 2
        flow: pill.vertical ? GridLayout.TopToBottom : GridLayout.LeftToRight
        rows: pill.vertical ? -1 : 1
        columns: pill.vertical ? 1 : -1
        rowSpacing: 6
        columnSpacing: 6
        Text {
            visible: pill.movable && !pill.bare
            // the grip: drag the pill by it (or by any empty part of the pill) to another edge, or into the middle
            text: "⠿"
            color: studio.colors.faint; font.pixelSize: 14
            Layout.leftMargin: pill.vertical ? 4 : 6
            Layout.alignment: pill.vertical ? Qt.AlignLeft : Qt.AlignVCenter
        }
    }
}
