// The command palette: type to find anything the Studio can do, Enter to do it. Pages, the bot's controls, the tools,
// themes, other bots, the bot's actions and its targets. Each command says its key when it has one.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

MenuPanel {
    id: palette
    parent: Overlay.overlay
    modal: true
    x: (parent.width - width) / 2
    y: Math.round(parent.height * 0.14)
    width: Math.min(620, parent.width - 80)
    height: Math.min(460, search.height + list.contentHeight + 30)
    // ready before it shows: whatever's typed as it fades in counts
    onAboutToShow: { search.text = ""; list.currentIndex = 0; commands = build(); search.forceActiveFocus() }

    property var commands: []
    readonly property var shown: {
        var words = search.text.toLowerCase().trim().split(/\s+/).filter(function (word) { return word !== "" })
        return commands.filter(function (one) {
            var text = (one.label + " " + one.group).toLowerCase()
            return words.every(function (word) { return text.indexOf(word) >= 0 })
        }).slice(0, 40)
    }
    function key(action) { return studio.keys[action] ? Format.sequence(studio.keys[action]) : "" }
    function build() {
        var found = [
            { group: "Go to", label: "Overview", icon: "▤", hint: key("page.overview"), run: function () { window.go("overview") } },
            { group: "Go to", label: "Library", icon: "▦", hint: key("page.library"), run: function () { window.go("library") } },
            { group: "Go to", label: "Results", icon: "▥", hint: key("page.results"), run: function () { window.go("results") } },
            { group: "Go to", label: "Settings", icon: "≡", hint: key("page.settings"), run: function () { window.go("settings") } },
            { group: "Go to", label: "darbit settings", icon: "◐", hint: key("page.darbit"), run: function () { window.go("studio") } },
            { group: "Tools", label: "Capture", icon: "▣", hint: key("capture.freeze"), run: function () { studio.openCapture("any") } },
            { group: "Tools", label: "Record an action", icon: "●", hint: "", run: function () { window.go("library"); window.recordAction("") } },
            { group: "Tools", label: "Highlight the last image", icon: "◎", hint: key("highlight.toggle"), run: function () { studio.toggleHighlight() } },
            { group: "Bots", label: "New bot", icon: "+", hint: key("bot.new"), run: function () { window.newBot("new") } }
        ]
        if (studio.bot.path) {
            if (window.running) {
                found.unshift({ group: "Bot", label: "Stop " + studio.bot.name, icon: "■", hint: "", run: function () { studio.stop() } })
                found.unshift({ group: "Bot", label: (studio.bot.status === "paused" ? "Go on with " : "Pause ") + studio.bot.name, icon: "❚❚", hint: "", run: function () { studio.pause() } })
            } else {
                found.unshift({ group: "Bot", label: "Play " + studio.bot.name, icon: "▶", hint: key("run.toggle"), run: function () { studio.start() } })
            }
        }
        var themes = [["glass-dark", "Glass dark"], ["glass-light", "Glass light"], ["midnight", "Midnight"], ["high-contrast", "High contrast"]]
        themes.forEach(function (one) {
            found.push({ group: "Theme", label: one[1], icon: "◐", hint: "", run: function () { studio.setTheme(one[0]) } })
        })
        studio.bots.forEach(function (bot) {
            if (bot.path !== studio.bot.path)
                found.push({ group: "Bots", label: "Switch to " + bot.name, icon: "⇄", hint: "", run: function () { studio.selectBot(bot.path) } })
        })
        studio.actions.forEach(function (action) {
            found.push({ group: "Action", label: "Play " + action.name, icon: "▶", hint: "", run: function () { studio.playAction(action.name) } })
            found.push({ group: "Action", label: "Open " + action.name, icon: "≡", hint: "", run: function () { window.openAction(action.name) } })
        })
        studio.library.forEach(function (asset) {
            found.push({ group: asset.kind, label: "Retake " + asset.name, icon: "▣", hint: "", run: function () { studio.retake(asset.name, asset.kind) } })
        })
        return found
    }
    function runAt(index) {
        var one = shown[index]
        if (!one) return
        palette.close()
        one.run()
    }

    contentItem: Column {
        spacing: 8
        Field {
            id: search
            objectName: "paletteSearch"
            width: parent.width; height: 42
            round: true; icon: "⌕"
            placeholderText: "Type a command, a page, an action or an image"
            font.pixelSize: 15
            onTextChanged: list.currentIndex = 0
            onAccepted: palette.runAt(list.currentIndex)
            Keys.onDownPressed: list.currentIndex = Math.min(list.count - 1, list.currentIndex + 1)
            Keys.onUpPressed: list.currentIndex = Math.max(0, list.currentIndex - 1)
            Keys.onEscapePressed: palette.close()
        }
        Text { visible: palette.shown.length === 0; text: "Nothing matches."; color: studio.colors.muted; font.pixelSize: 13; leftPadding: 12 }
        ListView {
            id: list
            width: parent.width
            height: Math.min(contentHeight, 380)
            clip: true
            model: palette.shown
            highlightMoveDuration: studio.effects ? 80 : 0
            SmoothWheel { view: list }
            delegate: Rectangle {
                required property var modelData
                required property int index
                width: list.width; height: 40; radius: 10
                color: ListView.isCurrentItem ? studio.colors.raisedHover : area.containsMouse ? studio.colors.raised : "transparent"
                RowLayout {
                    anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
                    spacing: 10
                    Text { text: modelData.icon; color: studio.colors.accent; font.pixelSize: 13; font.family: studio.symbols; Layout.preferredWidth: 18 }
                    Text { text: modelData.label; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.fillWidth: true; elide: Text.ElideRight }
                    Text { visible: modelData.hint !== ""; text: modelData.hint; color: studio.colors.muted; font.pixelSize: 11; font.family: "monospace" }
                    Text { text: modelData.group; color: studio.colors.faint; font.pixelSize: 11 }
                }
                MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: palette.runAt(index) }
            }
        }
    }
}
