// The Studio's own settings, behind the gear: the theme.
import QtQuick
import QtQuick.Controls.Basic

Pill {
    IconButton {
        id: gear
        glyph: "⚙"
        tip: "darbit Studio: theme"
        onClicked: menu.open()
        Menu {
            id: menu
            y: gear.height + 14
            x: gear.width - 230
            background: Rectangle { implicitWidth: 230; radius: 12; color: studio.colors.glassStrong; border.color: studio.colors.line }
            Repeater {
                model: [
                    { name: "glass-dark", label: "Glass dark" },
                    { name: "glass-light", label: "Glass light" },
                    { name: "midnight", label: "Midnight (lightest to draw)" },
                    { name: "high-contrast", label: "High contrast" }
                ]
                delegate: MenuItem {
                    required property var modelData
                    text: (studio.themeName === modelData.name ? "✓  " : "     ") + modelData.label
                    onTriggered: studio.setTheme(modelData.name)
                    contentItem: Text { text: parent.text; color: studio.colors.text; leftPadding: 6 }
                    background: Rectangle { color: parent.highlighted ? studio.colors.raisedHover : "transparent"; radius: 8 }
                }
            }
        }
    }
}
