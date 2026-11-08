// Scout's pill: the shared pill on a screen edge while Scout is on, like the run pill. How many of the bot's images
// have been seen this session, how many are weak or not seen yet, how long a pass takes, then Hide (back to the game)
// and ⤢ (back to the Studio): a row on the top and bottom edges, a labelled column on the sides, a card floating.
// Docked, it slides out of sight a few seconds after the mouse leaves it; the mouse at its edge brings it back. The
// boxes on the game (ScoutWindow) still let every click through.
import QtQuick
import QtQuick.Layouts
import "format.js" as Format

PillWindow {
    id: scoutPill
    hiding: scoutHiding
    place: scoutPlace
    title: "darbit Scout pill"
    cardWidth: 380
    readonly property bool column: form === "column"
    readonly property string seen: "Scout: " + scout.seen + " of " + scout.total + " seen"
    readonly property string took: Math.round(scout.took) + " ms"

    Row {
        visible: !scoutPill.column
        Layout.leftMargin: 4; Layout.rightMargin: 6
        spacing: 9
        Rectangle { width: 11; height: 11; radius: 5.5; color: studio.colors.ok; anchors.verticalCenter: parent.verticalCenter }
        Text {
            objectName: "scoutSeen"
            text: scoutPill.seen
            color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold
            anchors.verticalCenter: parent.verticalCenter
        }
        Chip { visible: scout.weak > 0; height: 22; tone: "warn"; text: scout.weak + " weak"; anchors.verticalCenter: parent.verticalCenter }
        Chip { visible: scout.notSeen > 0; height: 22; text: scout.notSeen + " not yet"; anchors.verticalCenter: parent.verticalCenter }
        Text {
            text: "· " + scoutPill.took
            color: studio.colors.muted; font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Column {
        visible: scoutPill.column
        Layout.preferredWidth: 128; Layout.leftMargin: 4
        spacing: 3
        Row {
            spacing: 8
            Rectangle { width: 10; height: 10; radius: 5; color: studio.colors.ok; anchors.verticalCenter: parent.verticalCenter }
            Text { text: "Scout"; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.Bold }
        }
        Text { text: scout.seen + " of " + scout.total + " seen"; color: studio.colors.muted; font.pixelSize: 13 }
        Text { visible: scout.weak > 0; text: scout.weak + " weak"; color: studio.colors.warn; font.pixelSize: 13 }
        Text { text: scoutPill.took + " a pass"; color: studio.colors.faint; font.family: "monospace"; font.pixelSize: 12 }
    }
    Rectangle {
        Layout.preferredWidth: scoutPill.column ? 128 : 1; Layout.preferredHeight: scoutPill.column ? 1 : 24
        Layout.topMargin: scoutPill.column ? 4 : 0; Layout.bottomMargin: scoutPill.column ? 4 : 0
        color: studio.colors.line
    }
    PillAction { labelled: scoutPill.column; glyph: "✕"; label: "Hide"; tip: studio.keys["scout.toggle"] ? "Hide Scout (" + Format.sequence(studio.keys["scout.toggle"]) + ")" : "Hide Scout"; onClicked: scout.stop() }
    PillAction { labelled: scoutPill.column; glyph: "⤢"; label: "Studio"; tip: "Open darbit Studio"; onClicked: studio.toggleScout() }

    heading: [
        Rectangle { width: 11; height: 11; radius: 5.5; color: studio.colors.ok },
        Text { text: scoutPill.seen; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold },
        Item { Layout.fillWidth: true },
        Text { text: scoutPill.took + " a pass"; color: studio.colors.muted; font.family: "monospace"; font.pixelSize: 12 }
    ]
    card: [
        Column {
            width: parent.width; spacing: 6
            Bar { width: parent.width; gradientFill: true; share: scout.total ? scout.seen / scout.total : 0 }
            Row {
                spacing: 8
                Chip { tone: "ok"; text: scout.seen + " seen" }
                Chip { tone: "warn"; text: scout.weak + " weak" }
                Chip { text: scout.notSeen + " not seen yet" }
            }
        },
        RowLayout {
            width: parent.width; spacing: 8
            PillButton { small: true; icon: "✕"; text: "Hide"; onClicked: scout.stop() }
            PillButton { small: true; kind: "quiet"; text: "Reset the session"; onClicked: scout.reset() }
            Item { Layout.fillWidth: true }
            PillButton { small: true; icon: "⤢"; text: "Open Studio"; onClicked: studio.toggleScout() }
        }
    ]
}
