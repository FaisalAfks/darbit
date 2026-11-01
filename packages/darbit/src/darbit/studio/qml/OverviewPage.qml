// The Overview: what the bot is doing now, what needs you, then today's round beside progress, what's next and gains.
// Everything comes from the bot's run report (d.step, d.plan, d.progress, d.next, d.record.gain).
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

Flickable {
    id: page
    contentHeight: column.height + 60
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {}

    function tile(kind) {
        var tiles = studio.overview
        for (var index = 0; index < tiles.length; index++)
            if (tiles[index].kind === kind) return tiles[index].data
        return null
    }
    readonly property var now: tile("now")
    readonly property var round: tile("round")
    readonly property var progress: tile("progress")
    readonly property var gains: tile("gains")
    readonly property var upcoming: tile("next")
    readonly property var failures: tile("failures")
    readonly property var setup: tile("setup")
    readonly property bool empty: studio.bots.length === 0
    readonly property bool running: studio.bot.status === "running" || studio.bot.status === "paused"
    readonly property var steps: now && now.path ? now.path.map(function (step) { return String(step).split(" > ").pop() }) : []
    readonly property var lastFailure: failures && failures.items.length ? failures.items[failures.items.length - 1] : null

    ColumnLayout {
        id: column
        x: 24; width: page.width - 48
        spacing: 16

        // ---- the first time: no bots yet
        Glass {
            visible: page.empty
            Layout.fillWidth: true; Layout.preferredHeight: 300
            padding: 34
            content: Item {
                anchors.fill: parent
                Image {
                    id: mark
                    source: "../logo.png"; width: 120; height: 120; sourceSize: Qt.size(240, 240); smooth: true
                    anchors.verticalCenter: parent.verticalCenter
                }
                Column {
                    anchors { left: mark.right; leftMargin: 34; right: parent.right; verticalCenter: parent.verticalCenter }
                    spacing: 12
                    Text { text: "WELCOME TO DARBIT"; color: studio.colors.accent; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.3 }
                    Text { text: "Make your first bot"; color: studio.colors.text; font.pixelSize: 32; font.weight: Font.Bold }
                    Text {
                        width: parent.width
                        text: "A bot is a folder of plain Python and the pictures it looks for. Start one from the template, install one from its git link, or add a folder you already have."
                        color: studio.colors.muted; font.pixelSize: 14; wrapMode: Text.WordWrap
                    }
                    Item { width: 1; height: 6 }
                    Row {
                        spacing: 10
                        PillButton { kind: "primary"; icon: "+"; text: "New bot"; onClicked: window.newBot("new") }
                        PillButton { icon: "⇩"; text: "From a git link"; onClicked: window.newBot("link") }
                        PillButton { kind: "quiet"; icon: "▤"; text: "Add a folder"; onClicked: window.newBot("folder") }
                    }
                }
            }
        }

        // ---- now
        Glass {
            id: hero
            visible: !page.empty
            Layout.fillWidth: true; Layout.preferredHeight: 196
            padding: 26
            content: Item {
                anchors.fill: parent
                Text {
                    text: page.running ? "NOW · " + (studio.bot.status === "paused" ? "PAUSED" : "RUNNING " + Format.duration(studio.now - (studio.bot.since || studio.now)).toUpperCase())
                                       : "NOW"
                    color: studio.bot.status === "paused" ? studio.colors.warn : page.running ? studio.colors.ok : studio.colors.muted
                    font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.3
                }
                Flow {
                    id: crumbs
                    y: 26; width: parent.width - 220
                    spacing: 10
                    visible: page.steps.length > 0
                    Repeater {
                        model: page.steps
                        delegate: Row {
                            required property var modelData
                            required property int index
                            spacing: 10
                            Text { visible: index > 0; text: "›"; color: studio.colors.faint; font.pixelSize: 30; anchors.verticalCenter: parent.verticalCenter }
                            Text {
                                text: modelData
                                color: index === page.steps.length - 1 ? studio.colors.accent : studio.colors.text
                                font.pixelSize: 32; font.weight: Font.Bold
                            }
                        }
                    }
                }
                Text {
                    visible: page.steps.length === 0
                    y: 26
                    text: page.running ? "Starting…" : "Not running"
                    color: page.running ? studio.colors.text : studio.colors.muted
                    font.pixelSize: 32; font.weight: Font.Bold
                }
                Text {
                    y: 76; width: parent.width - 220
                    text: page.steps.length === 0 && !page.running ? "Press Play to start " + (studio.bot.name || "the bot") + ", or start it from a terminal: this page follows it either way."
                        : page.now && page.now.since ? "since " + Format.clock(page.now.since) + " · " + Format.duration(Format.since(page.now.since, studio.now)) + " in this step" : ""
                    color: studio.colors.muted; font.pixelSize: 14; elide: Text.ElideRight
                }
                // the round as segments: done, running, to come
                Row {
                    visible: page.round !== null
                    anchors.bottom: parent.bottom
                    width: parent.width - 220
                    spacing: 6
                    Repeater {
                        model: page.round ? page.round.steps : []
                        delegate: Rectangle {
                            required property var modelData
                            width: (parent.width - 6 * ((page.round ? page.round.steps.length : 1) - 1)) / Math.max(1, page.round ? page.round.steps.length : 1)
                            height: 6; radius: 3
                            color: modelData.state === "ok" ? studio.colors.ok : modelData.state === "running" ? studio.colors.accent
                                : modelData.state === "failed" ? studio.colors.danger : studio.colors.raisedHover
                        }
                    }
                }
                // the main progress, as a ring
                Ring {
                    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                    width: 132; height: 132; thickness: 11
                    visible: page.ringItem() !== null
                    done: page.ringItem() ? page.ringItem().done : 0
                    total: page.ringItem() ? page.ringItem().total : 1
                    caption: page.ringItem() ? page.ringItem().label : ""
                }
            }
        }

        // ---- what needs you
        Banner {
            readonly property int missing: page.setup && page.setup.total ? page.setup.total - page.setup.done : 0
            visible: missing > 0
            Layout.fillWidth: true
            tone: "warn"; icon: "▣"
            title: missing + (missing === 1 ? " picture" : " pictures") + " to take before the bot can run"
            detail: page.setup && page.setup.current ? "Next: " + page.setup.current.name + " on " + page.setup.current.screen : ""
            action: "Start setup"
            onActed: studio.openCapture("guide")
        }
        Banner {
            visible: page.lastFailure !== null
            Layout.fillWidth: true
            tone: "danger"; icon: "!"
            title: page.lastFailure ? page.lastFailure.step + ": " + (page.lastFailure.reason || "failed") : ""
            detail: page.lastFailure ? "at " + Format.clock(page.lastFailure.time) + (page.failures.items.length > 1 ? " · " + page.failures.items.length + " problems today" : "") : ""
            action: "See in Results"
            onActed: window.go("results")
        }

        // ---- the round, and the rest
        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            Glass {
                title: "Today's round"
                delay: 60
                note: page.round ? page.doneCount() + " of " + page.round.steps.length : ""
                visible: page.round !== null
                Layout.fillWidth: true; Layout.preferredWidth: 6; Layout.alignment: Qt.AlignTop
                Layout.preferredHeight: 72 + (page.round ? page.round.steps.length : 0) * 48
                content: Column {
                    width: parent.width
                    Repeater {
                        model: page.round ? page.round.steps : []
                        delegate: Rectangle {
                            required property var modelData
                            width: parent.width; height: 48; radius: 12
                            color: modelData.state === "running" ? Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.09) : "transparent"
                            RowLayout {
                                anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
                                spacing: 14
                                Rectangle {
                                    width: 10; height: 10; radius: 5
                                    color: modelData.state === "ok" ? studio.colors.ok : modelData.state === "running" ? studio.colors.accent
                                        : modelData.state === "failed" ? studio.colors.danger : studio.colors.faint
                                }
                                Text { text: modelData.name; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.DemiBold; Layout.fillWidth: true; elide: Text.ElideRight }
                                Text {
                                    text: modelData.state === "planned" ? "later"
                                        : modelData.state === "running" ? "running"
                                        : modelData.state === "failed" ? (modelData.reason || "failed")
                                        : Format.clock(modelData.started) + (modelData.seconds ? " · " + Format.duration(modelData.seconds) : "")
                                    color: modelData.state === "running" ? studio.colors.accent : modelData.state === "failed" ? studio.colors.danger : studio.colors.muted
                                    font.pixelSize: 13; font.weight: modelData.state === "running" ? Font.DemiBold : Font.Normal
                                }
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true; Layout.preferredWidth: 5; Layout.alignment: Qt.AlignTop
                spacing: 16
                Glass {
                    title: "Progress"
                    delay: 100
                    visible: page.barItems().length > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70 + page.barItems().length * 44
                    content: Column {
                        width: parent.width
                        Repeater {
                            model: page.barItems()
                            delegate: RowLayout {
                                required property var modelData
                                width: parent.width; height: 44; spacing: 14
                                Text { text: modelData.label; color: studio.colors.text; font.pixelSize: 14; Layout.fillWidth: true; elide: Text.ElideRight }
                                Bar { Layout.preferredWidth: 130; share: modelData.total > 0 ? modelData.done / modelData.total : 0; gradientFill: true }
                                Text { text: modelData.done + " / " + modelData.total; color: studio.colors.muted; font.pixelSize: 13; Layout.preferredWidth: 54; horizontalAlignment: Text.AlignRight }
                            }
                        }
                    }
                }
                Glass {
                    title: "Next up"
                    delay: 140
                    visible: page.upcoming !== null
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70 + (page.upcoming ? page.upcoming.items.length : 0) * 44
                    content: Column {
                        width: parent.width
                        Repeater {
                            model: page.upcoming ? page.upcoming.items : []
                            delegate: RowLayout {
                                required property var modelData
                                width: parent.width; height: 44; spacing: 12
                                Text { text: "◷"; color: studio.colors.faint; font.pixelSize: 14 }
                                Column {
                                    Layout.fillWidth: true
                                    Text { text: modelData.label; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold }
                                    Text { text: Format.clock(modelData.at); color: studio.colors.faint; font.pixelSize: 12 }
                                }
                                Text { text: "in " + Format.duration(modelData.in_seconds); color: studio.colors.accent; font.pixelSize: 15; font.weight: Font.Bold }
                            }
                        }
                    }
                }
                Glass {
                    title: "Gains today"
                    delay: 180
                    visible: page.gains !== null
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70 + (page.gains ? page.gains.items.length : 0) * 42
                    content: Column {
                        width: parent.width
                        Repeater {
                            model: page.gains ? page.gains.items : []
                            delegate: RowLayout {
                                required property var modelData
                                width: parent.width; height: 42; spacing: 12
                                Rectangle { width: 10; height: 10; rotation: 45; radius: 2; color: studio.colors.accent2 }
                                Text { text: modelData.name; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.fillWidth: true }
                                Text { text: "+" + modelData.today; color: studio.colors.ok; font.pixelSize: 15; font.weight: Font.Bold }
                                Text {
                                    visible: modelData.total !== null
                                    text: modelData.total !== null ? Number(modelData.total).toLocaleString(Qt.locale(), "f", 0) : ""
                                    color: studio.colors.faint; font.pixelSize: 13
                                    Layout.preferredWidth: 70; horizontalAlignment: Text.AlignRight
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    function doneCount() {
        var done = 0
        for (var index = 0; index < round.steps.length; index++)
            if (round.steps[index].state === "ok") done++
        return done
    }
    function ringItem() {
        if (!progress) return null
        var best = null
        for (var index = 0; index < progress.items.length; index++) {
            var item = progress.items[index]
            if (item.total > 1 && (best === null || item.total > best.total)) best = item
        }
        return best
    }
    function barItems() {
        if (!progress) return []
        var ring = ringItem()
        return progress.items.filter(function (item) { return item !== ring })
    }
}
