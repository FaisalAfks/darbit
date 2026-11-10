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
    readonly property bool narrow: width < 1180
    readonly property bool running: studio.bot.status === "running" || studio.bot.status === "paused"

    Timer { interval: 1000; running: window.running && studio.shown; repeat: true; onTriggered: studio.tick() }
    Component.onCompleted: studio.connect()
    Connections {
        target: studio
        function onMadeBot(name) { toast.show(name + " is ready") }
        function onSaid(text) { toast.show(text) }
        function onChecksFound() { checksSheet.make().open() }
        function onAskedToReplace() { stopAndStartSheet.make().open() }
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
            onAddBot: newBotSheet.make().open()
            onOpenStudio: window.go("studio")
        }

        Item {
            Layout.fillWidth: true; Layout.fillHeight: true

            TopBar {
                id: top
                x: 24; y: 16; width: parent.width - 48
                page: window.page
                onPicked: function (name) { window.go(name) }
                onAddBot: newBotSheet.make().open()
                onOpenStudio: window.go("studio")
            }

            // the pages, one shown at a time; the one leaving fades out under the next (PageFrame)
            Item {
                id: stack
                anchors { left: parent.left; right: parent.right; top: top.bottom; bottom: parent.bottom; topMargin: 16 }
                PageFrame { anchors.fill: parent; shown: window.page === "overview"; source: "OverviewPage.qml" }
                PageFrame { anchors.fill: parent; shown: window.page === "library"; source: "LibraryPage.qml" }
                PageFrame { anchors.fill: parent; shown: window.page === "results"; source: "ResultsPage.qml" }
                PageFrame { anchors.fill: parent; shown: window.page === "settings"; source: "SettingsPage.qml" }
                PageFrame { anchors.fill: parent; shown: window.page === "studio"; source: "StudioPage.qml" }
                PageFrame { anchors.fill: parent; shown: window.page === "action"; source: "ActionPage.qml" }
            }
        }
    }

    Toast { id: toast }
    // the sheets, the palette and the tools' windows are made the first time they're wanted (OnFirstUse): the Studio
    // starts with none of them
    OnFirstUse { id: palette; source: "CommandPalette.qml" }
    OnFirstUse { id: newBotSheet; source: "NewBotSheet.qml" }
    OnFirstUse { id: recordSheet; source: "RecordSheet.qml" }
    OnFirstUse { id: checksSheet; source: "ChecksSheet.qml" }
    OnFirstUse { id: stopAndStartSheet; source: "StopAndStartSheet.qml" }
    OnFirstUse { source: "CaptureWindow.qml"; wanted: capture.isOpen }
    OnFirstUse { source: "RecorderPill.qml"; wanted: recorderHiding.isOpen }
    OnFirstUse { source: "ScoutWindow.qml"; wanted: scout.isOn }
    OnFirstUse { source: "ScoutPill.qml"; wanted: scoutHiding.isOpen }
    OnFirstUse { source: "GhostWindow.qml"; wanted: studio.ghost && ghost.marks.length > 0 }
    OnFirstUse { source: "RunPill.qml"; wanted: runPill.isOpen }
    OnFirstUse { source: "TrayPanel.qml"; wanted: window.trayWanted }
    property bool trayWanted: false  // app.py, the first time the tray icon is clicked

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
    Shortcut { sequence: window.keyOf("bot.new"); onActivated: newBotSheet.make().open() }
    Shortcut { sequence: window.keyOf("palette.open"); onActivated: window.openPalette() }
    function openPalette() { palette.make().open() }
    function newBot(way) { var sheet = newBotSheet.make(); sheet.way = way || "new"; sheet.open() }
    function recordAction(name) { recordSheet.make().openFor(name || "") }
    function openAction(name) { studio.openAction(name); page = "action" }
    Shortcut { sequence: window.keyOf("run.toggle"); onActivated: window.running ? null : studio.play() }
}
