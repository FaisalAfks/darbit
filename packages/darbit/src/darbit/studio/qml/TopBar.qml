// The top bar: the chosen bot (or the bot menu, without the sidebar), its pages, and its run control.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Item {
    id: bar
    property string page: "overview"
    signal picked(string name)
    signal addBot()
    signal openStudio()
    height: 52

    RowLayout {
        anchors.fill: parent
        spacing: 14

        BotPicker {
            visible: !studio.sidebar
            onAddBot: bar.addBot()
            onOpenStudio: bar.openStudio()
        }
        Row {
            visible: studio.sidebar && bar.page !== "studio"
            spacing: 12
            Avatar { name: studio.bot.name || ""; accent: studio.bot.accent || ""; icon: studio.bot.icon || ""; size: 40; anchors.verticalCenter: parent.verticalCenter }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    objectName: "barName"
                    width: Math.min(implicitWidth, 280)
                    elide: Text.ElideRight
                    text: studio.bot.name || "No bots yet"; color: studio.colors.text; font.pixelSize: 17; font.weight: Font.Bold
                    // a name too long for the bar: whole on hover
                    HoverHandler { id: nameHover }
                    ToolTip.visible: nameHover.hovered && truncated
                    ToolTip.text: text
                    ToolTip.delay: 400
                }
                Text { text: studio.bot.version ? "v" + studio.bot.version : ""; visible: text !== ""; color: studio.colors.faint; font.pixelSize: 12 }
            }
        }
        Text {
            visible: bar.page === "studio"
            text: "darbit settings"; color: studio.colors.text; font.pixelSize: 20; font.weight: Font.Bold
        }

        Item { Layout.fillWidth: true }

        Segmented {
            visible: !!studio.bot.path
            current: bar.page === "action" ? "library" : bar.page
            model: [
                { key: "overview", label: "Overview" },
                { key: "library", label: "Library" },
                { key: "results", label: "Results" },
                { key: "settings", label: "Settings" }
            ]
            onPicked: function (key) { bar.picked(key) }
        }

        Item { Layout.fillWidth: true }

        RunControl { visible: !!studio.bot.path }
    }
}
