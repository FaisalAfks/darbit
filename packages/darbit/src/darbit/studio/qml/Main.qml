// darbit Studio's window: the bots (a sidebar, or a menu in the top bar), the chosen bot's pages and its run control.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

ApplicationWindow {
    id: window
    width: 1400; height: 880
    minimumWidth: 900; minimumHeight: 600
    // shown by app.py once it's in its place
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
        function onChecksFound() { checksSheet.open() }
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
                PageFrame { source: "OverviewPage.qml" }
                PageFrame { source: "LibraryPage.qml" }
                PageFrame { source: "ResultsPage.qml" }
                PageFrame { source: "SettingsPage.qml" }
                PageFrame { source: "StudioPage.qml" }
                PageFrame { source: "ActionPage.qml" }
            }
        }
    }

    Toast { id: toast }
    CommandPalette { id: palette; objectName: "commandPalette" }
    NewBotSheet { id: sheet }
    RecordSheet { id: recordSheet }
    ChecksSheet { id: checksSheet }
    CaptureWindow { objectName: "captureWindow" }
    RecorderPill { objectName: "recorderPill" }
    ScoutWindow { objectName: "scoutWindow" }
    ScoutPill { objectName: "scoutPill" }
    GhostWindow { objectName: "ghostWindow" }
    RunPill { objectName: "runPill" }

    function go(name) {
        page = name
        if (name === "overview") studio.loadOverview()
        else if (name === "library") { studio.loadLibrary(); studio.loadActions() }
        else if (name === "results") studio.loadDays()
        else if (name === "settings") studio.loadSettings()
    }

    function keyOf(action) { return Format.sequence(studio.keys[action]) }
    Shortcut { sequence: window.keyOf("page.overview"); onActivated: window.go("overview") }
    Shortcut { sequence: window.keyOf("page.library"); onActivated: window.go("library") }
    Shortcut { sequence: window.keyOf("page.results"); onActivated: window.go("results") }
    Shortcut { sequence: window.keyOf("page.settings"); onActivated: window.go("settings") }
    Shortcut { sequence: window.keyOf("page.darbit"); onActivated: window.go("studio") }
    Shortcut { sequence: window.keyOf("bot.new"); onActivated: sheet.open() }
    Shortcut { sequence: window.keyOf("palette.open"); onActivated: palette.open() }
    function newBot(way) { sheet.way = way || "new"; sheet.open() }
    function recordAction(name) { recordSheet.openFor(name || "") }
    function openAction(name) { studio.openAction(name); page = "action" }
    Shortcut { sequence: window.keyOf("run.toggle"); onActivated: window.running ? null : studio.play() }
}
