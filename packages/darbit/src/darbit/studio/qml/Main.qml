// darbit Studio's window: the bot picker, the page bar and the run controls on top, the chosen page below.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

ApplicationWindow {
    id: window
    width: 1400; height: 880
    minimumWidth: 960; minimumHeight: 620
    visible: true
    title: "darbit Studio"
    color: studio.colors.bg
    font.pixelSize: 14

    property string page: "overview"
    readonly property var bot: studio.bot
    readonly property bool running: bot.status === "running" || bot.status === "paused"

    Timer { interval: 1000; running: window.running; repeat: true; onTriggered: studio.tick() }
    Component.onCompleted: studio.connect()

    Backdrop { anchors.fill: parent }

    // ---- the top bar
    Item {
        id: top
        x: 24; y: 18
        width: parent.width - 48; height: 52

        BotPicker { id: picker; anchors.left: parent.left }

        Pill {
            anchors.horizontalCenter: parent.horizontalCenter
            Tab { icon: "◉"; label: "Overview"; current: window.page === "overview"; onClicked: window.go("overview") }
            Tab { icon: "▣"; label: "Library"; current: window.page === "library"; onClicked: window.go("library") }
            Tab { icon: "≡"; label: "Runs"; current: window.page === "runs"; onClicked: window.go("runs") }
            Tab { icon: "⚙"; label: "Settings"; current: window.page === "settings"; onClicked: window.go("settings") }
        }

        RunPill { anchors.right: parent.right }
    }

    // ---- the page
    StackLayout {
        id: pages
        anchors { left: parent.left; right: parent.right; top: top.bottom; bottom: parent.bottom; topMargin: 18 }
        currentIndex: ["overview", "library", "runs", "settings"].indexOf(window.page)
        OverviewPage {}
        LibraryPage {}
        RunsPage {}
        SettingsPage {}
    }

    // ---- what went wrong, if anything
    Rectangle {
        visible: studio.message !== ""
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 24 }
        width: Math.min(text.implicitWidth + 40, parent.width - 80); height: 44; radius: 22
        color: studio.colors.glassStrong
        border.color: studio.colors.danger
        Text {
            id: text
            anchors.centerIn: parent
            width: Math.min(implicitWidth, parent.width - 40)
            elide: Text.ElideRight
            text: studio.message
            color: studio.colors.text
        }
    }

    function go(name) {
        page = name
        if (name === "overview") studio.loadOverview()
        else if (name === "library") studio.loadLibrary()
        else if (name === "runs") studio.loadDays()
        else if (name === "settings") studio.loadSettings()
    }

    CaptureWindow { objectName: "captureWindow" }

    Shortcut { sequence: "Ctrl+1"; onActivated: window.go("overview") }
    Shortcut { sequence: "Ctrl+2"; onActivated: window.go("library") }
    Shortcut { sequence: "Ctrl+3"; onActivated: window.go("runs") }
    Shortcut { sequence: "Ctrl+4"; onActivated: window.go("settings") }
}
