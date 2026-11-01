// darbit settings: the Studio's own, on this PC: the theme, the bot sidebar, smooth effects, and the version.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Flickable {
    id: page
    contentHeight: column.height + 80
    clip: true
    ScrollBar.vertical: ScrollBar {}

    readonly property var themes: [
        { key: "glass-dark", label: "Glass dark", bg: "#0b0d12", panel: "#1b1e27", a: "#5ac8fa", b: "#a78bfa" },
        { key: "glass-light", label: "Glass light", bg: "#e9edf3", panel: "#ffffff", a: "#0369a1", b: "#6d28d9" },
        { key: "midnight", label: "Midnight", bg: "#000000", panel: "#0d0f14", a: "#38bdf8", b: "#818cf8" },
        { key: "high-contrast", label: "High contrast", bg: "#000000", panel: "#000000", a: "#ffff00", b: "#00ffff" }
    ]

    ColumnLayout {
        id: column
        x: 24; width: Math.min(page.width - 48, 980)
        spacing: 18

        Glass {
            title: "Look"
            Layout.fillWidth: true; Layout.preferredHeight: 224
            content: Row {
                spacing: 14
                Repeater {
                    model: page.themes
                    delegate: Rectangle {
                        id: swatch
                        required property var modelData
                        readonly property bool on: studio.themeName === modelData.key
                        width: 190; height: 150; radius: 16
                        color: modelData.bg
                        border.color: on ? studio.colors.accent : studio.colors.line
                        border.width: on ? 2 : 1
                        scale: tap.containsMouse ? 1.03 : 1
                        Behavior on scale { NumberAnimation { duration: studio.effects ? 140 : 0; easing.type: Easing.OutCubic } }
                        Rectangle { x: 14; y: 14; width: 162; height: 70; radius: 10; color: modelData.panel; border.color: Qt.rgba(0.5, 0.5, 0.5, 0.25)
                            Rectangle { x: 12; y: 14; width: 70; height: 8; radius: 4; color: modelData.a }
                            Rectangle { x: 12; y: 32; width: 110; height: 6; radius: 3; color: modelData.b; opacity: 0.7 }
                            Rectangle { x: 12; y: 48; width: 90; height: 6; radius: 3; color: modelData.b; opacity: 0.4 } }
                        Text { x: 14; y: 100; text: modelData.label; color: modelData.key === "glass-light" ? "#111827" : "#eef1f6"; font.pixelSize: 14; font.weight: Font.DemiBold }
                        Text { x: 14; y: 120; visible: swatch.on; text: "✓ in use"; color: modelData.a; font.pixelSize: 12; font.weight: Font.DemiBold }
                        MouseArea { id: tap; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: studio.setTheme(modelData.key) }
                    }
                }
            }
        }

        Glass {
            title: "Window"
            delay: 60
            Layout.fillWidth: true; Layout.preferredHeight: 200
            content: Column {
                width: parent.width; spacing: 12
                Choice {
                    width: parent.width
                    label: "Bots in a sidebar"
                    help: "Every bot down the left side, folded to their squares on a narrow window. Off: a menu in the top bar."
                    checked: studio.sidebar
                    onToggled: function (on) { studio.setSidebar(on) }
                }
                Choice {
                    width: parent.width
                    label: "Smooth effects"
                    help: "Glass, and pages and cards that slide into place. Turn off on a slower PC: everything shows at once."
                    checked: studio.effects
                    onToggled: function (on) { studio.setEffects(on) }
                }
                Choice {
                    width: parent.width
                    label: "Ghost cursor"
                    help: "A ripple where a bot clicks and the keys it presses, over the game, so you can see what it's doing."
                    checked: studio.ghost
                    onToggled: function (on) { studio.setGhost(on) }
                }
            }
        }

        Text {
            Layout.leftMargin: 4
            text: "darbit " + studio.version + " · the service runs your bots: closing the Studio stops nothing"
            color: studio.colors.faint; font.pixelSize: 13
        }
    }
}
