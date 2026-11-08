// Highlight's pill: the shared pill on a screen edge while Highlight is on, like the run pill. What's found, how long a
// pass takes, look-alikes as a warning, then Hide (back to the game) and ⤢ (back to the Studio): a row on the top and
// bottom edges, a labelled column on the sides, a card floating. Docked, it slides out of sight a few seconds after
// the mouse leaves it; the mouse at its edge brings it back. The boxes on the game (HighlightWindow) still let every
// click through.
import QtQuick
import QtQuick.Layouts

PillWindow {
    id: highlightPill
    hiding: highlightHiding
    place: highlightPlace
    title: "darbit Highlight pill"
    cardWidth: 380
    readonly property bool column: form === "column"
    readonly property string found: highlight.found + " of " + highlight.boxes.length + " found"
    readonly property string took: Math.round(highlight.took) + " ms"
    readonly property string alike: highlight.alike + (highlight.alike === 1 ? " look-alike" : " look-alikes")

    Row {
        visible: !highlightPill.column
        Layout.leftMargin: 4; Layout.rightMargin: 6
        spacing: 9
        Rectangle { width: 11; height: 11; radius: 5.5; color: studio.colors.ok; anchors.verticalCenter: parent.verticalCenter }
        Text {
            text: "Highlight"
            color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            objectName: "highlightFound"
            text: highlightPill.found + " · " + highlightPill.took
            color: studio.colors.muted; font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
        Text {
            visible: highlight.alike > 0
            text: "⚠ " + highlightPill.alike
            color: studio.colors.warn; font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Column {
        visible: highlightPill.column
        Layout.preferredWidth: 128; Layout.leftMargin: 4
        spacing: 3
        Row {
            spacing: 8
            Rectangle { width: 10; height: 10; radius: 5; color: studio.colors.ok; anchors.verticalCenter: parent.verticalCenter }
            Text { text: "Highlight"; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold }
        }
        Text { text: highlightPill.found; color: studio.colors.muted; font.pixelSize: 13 }
        Text { text: highlightPill.took + " a pass"; color: studio.colors.faint; font.family: "monospace"; font.pixelSize: 12 }
        Text {
            visible: highlight.alike > 0
            text: "⚠ " + highlightPill.alike
            color: studio.colors.warn; font.pixelSize: 13
        }
    }
    Rectangle {
        Layout.preferredWidth: highlightPill.column ? 128 : 1; Layout.preferredHeight: highlightPill.column ? 1 : 24
        Layout.topMargin: highlightPill.column ? 4 : 0; Layout.bottomMargin: highlightPill.column ? 4 : 0
        color: studio.colors.line
    }
    PillAction { labelled: highlightPill.column; glyph: "✕"; label: "Hide"; tip: "Hide Highlight (Ctrl+Alt+H)"; onClicked: highlight.stop() }
    PillAction { labelled: highlightPill.column; glyph: "⤢"; label: "Studio"; tip: "Open darbit Studio"; onClicked: studio.toggleHighlight() }

    heading: [
        Rectangle { width: 11; height: 11; radius: 5.5; color: studio.colors.ok },
        Text { text: "Highlight"; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold },
        Item { Layout.fillWidth: true },
        Text { text: highlightPill.took + " a pass"; color: studio.colors.muted; font.family: "monospace"; font.pixelSize: 12 }
    ]
    card: [
        Column {
            width: parent.width; spacing: 6
            RowLayout {
                width: parent.width
                Text { text: "Found on screen"; color: studio.colors.text; font.pixelSize: 13; font.weight: Font.DemiBold; Layout.fillWidth: true }
                Text { text: highlightPill.found; color: studio.colors.muted; font.pixelSize: 12 }
            }
            Bar { width: parent.width; gradientFill: true; share: highlight.boxes.length ? highlight.found / highlight.boxes.length : 0 }
        },
        Text {
            visible: highlight.alike > 0
            width: parent.width; wrapMode: Text.Wrap
            text: "⚠ " + highlightPill.alike + ": images found on the same spot, marked on the screen"
            color: studio.colors.warn; font.pixelSize: 13
        },
        RowLayout {
            width: parent.width; spacing: 8
            PillButton { small: true; icon: "✕"; text: "Hide"; onClicked: highlight.stop() }
            Item { Layout.fillWidth: true }
            PillButton { small: true; icon: "⤢"; text: "Open Studio"; onClicked: studio.toggleHighlight() }
        }
    ]
}
