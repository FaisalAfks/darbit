// darbit Studio's window: the bots (a sidebar, or a menu in the top bar), the chosen bot's pages and its run control.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1400; height: 880
    minimumWidth: 900; minimumHeight: 600
    visible: true
    title: "darbit Studio"
    color: studio.colors.bg
    font.pixelSize: 14

    property string page: "overview"  // overview, library, results, settings, or studio (darbit's own settings)
    readonly property var pages: ["overview", "library", "results", "settings", "studio", "action"]
    readonly property bool narrow: width < 1180
    readonly property bool running: studio.bot.status === "running" || studio.bot.status === "paused"

    Timer { interval: 1000; running: window.running && window.visible; repeat: true; onTriggered: studio.tick() }
    Component.onCompleted: studio.connect()
    Connections {
        target: studio
        function onMadeBot(name) { toast.show(name + " is ready") }
        function onSaid(text) { toast.show(text) }
    }

    Backdrop { anchors.fill: parent }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Sidebar {
            id: sidebar
            visible: studio.sidebar
            folded: window.narrow
            Layout.fillHeight: true
            onAddBot: sheet.open()
            onOpenStudio: window.go("studio")
        }

        Item {
            Layout.fillWidth: true; Layout.fillHeight: true

            TopBar {
                id: top
                x: 24; y: 16; width: parent.width - 48
                page: window.page
                onPicked: function (name) { window.go(name) }
                onAddBot: sheet.open()
                onOpenStudio: window.go("studio")
            }

            StackLayout {
                id: stack
                anchors { left: parent.left; right: parent.right; top: top.bottom; bottom: parent.bottom; topMargin: 16 }
                currentIndex: window.pages.indexOf(window.page)
                PageFrame { OverviewPage { anchors.fill: parent } }
                PageFrame { LibraryPage { objectName: "libraryPage"; anchors.fill: parent } }
                PageFrame { ResultsPage { anchors.fill: parent } }
                PageFrame { SettingsPage { anchors.fill: parent } }
                PageFrame { StudioPage { anchors.fill: parent } }
                PageFrame { ActionPage { anchors.fill: parent } }
            }
        }
    }

    Toast { id: toast }
    NewBotSheet { id: sheet }
    RecordSheet { id: recordSheet }
    CaptureWindow { objectName: "captureWindow" }
    RecorderPill { objectName: "recorderPill" }
    HighlightWindow { objectName: "highlightWindow" }

    function go(name) {
        page = name
        if (name === "overview") studio.loadOverview()
        else if (name === "library") { studio.loadLibrary(); studio.loadActions() }
        else if (name === "results") studio.loadDays()
        else if (name === "settings") studio.loadSettings()
    }

    Shortcut { sequence: "Ctrl+1"; onActivated: window.go("overview") }
    Shortcut { sequence: "Ctrl+2"; onActivated: window.go("library") }
    Shortcut { sequence: "Ctrl+3"; onActivated: window.go("results") }
    Shortcut { sequence: "Ctrl+4"; onActivated: window.go("settings") }
    Shortcut { sequence: "Ctrl+,"; onActivated: window.go("studio") }
    Shortcut { sequence: "Ctrl+N"; onActivated: sheet.open() }
    function recordAction(name) { recordSheet.openFor(name || "") }
    function openAction(name) { studio.openAction(name); page = "action" }
    Shortcut { sequence: "F5"; onActivated: window.running ? null : studio.start() }
}
