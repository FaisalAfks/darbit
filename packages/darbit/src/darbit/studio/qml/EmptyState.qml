// What a page or list shows when it has nothing yet (#319): a soft glyph in a glass circle, a title, one line of why,
// and the main action with its key from the keymap ("or press Ctrl+Alt+C"). The action is a button, or a link for a
// way elsewhere ("See yesterday →"). It rises into place with the cards (CardMotion); `compact` is the size for a pill.
import QtQuick
import QtQuick.Shapes
import "format.js" as Format

Item {
    id: empty
    property string glyph: "◎"
    property string title: ""
    property string line: ""
    property string action: ""      // the main action's text; none without it
    property string actionIcon: ""
    property bool link: false       // the action as a link instead of a button
    property string keyName: ""     // the action's key in keymap.toml, shown under it
    property bool compact: false    // inside a pill
    property var tokens: studio.motion
    signal acted()

    readonly property string keys: keyName !== "" && studio.keys[keyName] ? Format.sequence(studio.keys[keyName]) : ""
    readonly property real ring: compact ? 48 : 78
    implicitWidth: compact ? 420 : 520
    implicitHeight: column.implicitHeight
    width: parent ? Math.min(parent.width, compact ? 420 : 520) : implicitWidth
    height: implicitHeight

    opacity: motion.fade
    transform: motion.moves
    CardMotion { id: motion; lifts: false; tokens: empty.tokens }

    Column {
        id: column
        width: empty.width
        spacing: empty.compact ? 6 : 8

        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: empty.ring; height: empty.ring
            Rectangle { anchors.fill: parent; radius: width / 2; color: studio.colors.glass }
            // the light in the glass: the accent from the top left into the second accent, fading out
            Loader {
                anchors.fill: parent
                active: empty.visible  // drawn only while it shows
                sourceComponent: Shape {
                    anchors.fill: parent
                    ShapePath {
                        strokeColor: "transparent"
                        fillGradient: RadialGradient {
                            centerX: empty.ring * 0.35; centerY: empty.ring * 0.3; centerRadius: empty.ring * 0.95
                            focalX: centerX; focalY: centerY
                            GradientStop { position: 0; color: Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.22) }
                            GradientStop { position: 0.6; color: Qt.rgba(studio.colors.accent2.r, studio.colors.accent2.g, studio.colors.accent2.b, 0.12) }
                            GradientStop { position: 0.7; color: "transparent" }
                        }
                        PathRectangle { width: empty.ring; height: empty.ring; radius: empty.ring / 2 }
                    }
                }
            }
            Rectangle { anchors.fill: parent; radius: width / 2; color: "transparent"; border.color: studio.colors.line }
            Text {
                anchors.centerIn: parent
                text: empty.glyph
                color: studio.colors.accent
                font.family: studio.symbols; font.pixelSize: empty.compact ? 20 : 30
            }
        }
        Item { width: 1; height: empty.compact ? 2 : 4 }
        Text {
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: empty.title
            color: studio.colors.text
            font.pixelSize: empty.compact ? 14 : 16; font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Text {
            visible: empty.line !== ""
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            text: empty.line
            color: studio.colors.muted
            font.pixelSize: empty.compact ? 12 : 13
        }
        Item { visible: empty.action !== ""; width: 1; height: 2 }
        PillButton {
            objectName: "emptyAction"
            visible: empty.action !== "" && !empty.link
            anchors.horizontalCenter: parent.horizontalCenter
            kind: "primary"; small: true
            icon: empty.actionIcon; text: empty.action
            onClicked: empty.acted()
        }
        Text {
            objectName: "emptyLink"
            visible: empty.action !== "" && empty.link
            anchors.horizontalCenter: parent.horizontalCenter
            text: empty.action + " →"
            color: studio.colors.accent
            font.pixelSize: 13; font.underline: linkArea.containsMouse
            MouseArea { id: linkArea; anchors.fill: parent; anchors.margins: -6; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: empty.acted() }
        }
        Text {
            visible: empty.action !== "" && empty.keys !== ""
            anchors.horizontalCenter: parent.horizontalCenter
            text: "or press " + empty.keys
            color: studio.colors.faint
            font.pixelSize: 12
        }
    }
}
