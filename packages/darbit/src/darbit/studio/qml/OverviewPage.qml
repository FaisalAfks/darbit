// The Overview: the bot, then its tiles from today's run report: now, progress, the round, next up, gains, failures.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

Flickable {
    id: page
    contentHeight: column.height + 120
    clip: true
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

    ColumnLayout {
        id: column
        x: 24; width: page.width - 48
        spacing: 20

        // ---- the bot
        RowLayout {
            Layout.fillWidth: true
            spacing: 16
            Avatar { name: studio.bot.name || ""; accent: studio.bot.accent || ""; size: 56 }
            Column {
                Layout.fillWidth: true
                Text { text: studio.bot.name || ""; color: studio.colors.text; font.pixelSize: 28; font.weight: Font.Bold }
                Text {
                    text: studio.bot.summary || ""
                    visible: text !== ""
                    color: studio.colors.muted; font.pixelSize: 15
                }
            }
            Chip { text: "v" + (studio.bot.version || "?"); visible: !!studio.bot.version }
        }

        // ---- now and progress
        RowLayout {
            Layout.fillWidth: true
            spacing: 20
            Glass {
                title: "Now"
                Layout.fillWidth: true; Layout.preferredWidth: 2; Layout.preferredHeight: 230
                Chip {
                    parent: parent
                    anchors { right: parent.right; top: parent.top; margins: 18 }
                    visible: !!(page.now && page.now.since) && studio.bot.status === "running"
                    tone: "info"
                    text: "FOR " + Format.duration(Format.since(page.now ? page.now.since : "", studio.now))
                }
                content: Column {
                    width: parent.width
                    spacing: 14
                    Flow {
                        width: parent.width
                        spacing: 10
                        Repeater {
                            model: page.nowSteps()
                            delegate: Row {
                                required property var modelData
                                required property int index
                                spacing: 10
                                Text {
                                    visible: index > 0; text: "›"; color: studio.colors.faint
                                    font.pixelSize: 26; anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: modelData
                                    color: index === page.nowSteps().length - 1 ? studio.colors.accent : studio.colors.text
                                    font.pixelSize: 28; font.weight: Font.Bold
                                }
                            }
                        }
                    }
                    Text {
                        text: page.nowSteps().length === 0
                            ? (studio.bot.status === "running" ? "Starting…" : "Not running. Press Play to start " + (studio.bot.name || "the bot") + ".")
                            : (page.round ? page.roundSummary() : "")
                        color: studio.colors.muted; font.pixelSize: 14
                        width: parent.width; wrapMode: Text.Wrap
                    }
                }
            }
            Glass {
                title: "Progress"
                visible: page.progress !== null
                Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.preferredHeight: 230
                content: RowLayout {
                    width: parent.width; height: parent.height
                    spacing: 22
                    Column {
                        visible: page.ringItem() !== null
                        spacing: 10
                        Ring {
                            done: page.ringItem() ? page.ringItem().done : 0
                            total: page.ringItem() ? page.ringItem().total : 1
                        }
                        Text {
                            text: page.ringItem() ? page.ringItem().label : ""
                            color: studio.colors.muted; font.pixelSize: 13
                            width: 120; wrapMode: Text.Wrap
                        }
                    }
                    Column {
                        Layout.fillWidth: true; Layout.alignment: Qt.AlignTop
                        spacing: 16
                        Repeater {
                            model: page.barItems()
                            delegate: Column {
                                required property var modelData
                                width: parent.width; spacing: 8
                                RowLayout {
                                    width: parent.width
                                    Text { text: modelData.label; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.fillWidth: true; elide: Text.ElideRight }
                                    Text { text: modelData.done + " / " + modelData.total; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold }
                                }
                                Bar { width: parent.width; share: modelData.total > 0 ? modelData.done / modelData.total : 0 }
                            }
                        }
                    }
                }
            }
        }

        // ---- the round and what's next
        RowLayout {
            Layout.fillWidth: true
            spacing: 20
            Glass {
                title: "Today's round"
                visible: page.round !== null
                Layout.fillWidth: true; Layout.preferredWidth: 6
                Layout.preferredHeight: 70 + (page.round ? page.round.steps.length : 0) * 48
                content: Column {
                    width: parent.width
                    Repeater {
                        model: page.round ? page.round.steps : []
                        delegate: Rectangle {
                            required property var modelData
                            width: parent.width; height: 46; radius: 10
                            color: modelData.state === "running" ? studio.colors.raised : "transparent"
                            RowLayout {
                                anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
                                spacing: 14
                                Rectangle {
                                    width: 10; height: 10; radius: 5
                                    color: modelData.state === "ok" ? studio.colors.ok : modelData.state === "running" ? studio.colors.info
                                        : modelData.state === "failed" ? studio.colors.danger : studio.colors.faint
                                }
                                Text { text: modelData.name; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.fillWidth: true }
                                Text {
                                    text: modelData.started ? Format.clock(modelData.started) + (modelData.seconds ? " · " + Format.duration(modelData.seconds) : modelData.state === "running" ? " · now" : "") : ""
                                    color: studio.colors.muted; font.pixelSize: 13
                                }
                                Chip {
                                    visible: modelData.state !== "planned"
                                    text: Format.stateText(modelData.state)
                                    tone: Format.tone(modelData.state)
                                }
                                Text { visible: modelData.state === "planned"; text: "next in this round"; color: studio.colors.muted; font.pixelSize: 13 }
                            }
                        }
                    }
                }
            }
            Glass {
                title: "Next up"
                visible: page.upcoming !== null
                Layout.fillWidth: true; Layout.preferredWidth: 5; Layout.alignment: Qt.AlignTop
                Layout.preferredHeight: 70 + (page.upcoming ? page.upcoming.items.length : 0) * 76
                content: Column {
                    width: parent.width; spacing: 12
                    Repeater {
                        model: page.upcoming ? page.upcoming.items : []
                        delegate: Rectangle {
                            required property var modelData
                            width: parent.width; height: 64; radius: 12
                            color: studio.colors.raised
                            Column {
                                anchors { left: parent.left; leftMargin: 16; verticalCenter: parent.verticalCenter }
                                Text { text: modelData.label; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.Bold }
                                Text { text: Format.clock(modelData.at); color: studio.colors.muted; font.pixelSize: 13 }
                            }
                            Text {
                                anchors { right: parent.right; rightMargin: 16; verticalCenter: parent.verticalCenter }
                                text: Format.duration(modelData.in_seconds)
                                color: studio.colors.accent; font.pixelSize: 17; font.weight: Font.Bold
                            }
                        }
                    }
                }
            }
        }

        // ---- gains and failures
        RowLayout {
            Layout.fillWidth: true
            spacing: 20
            Glass {
                title: "Gains today"
                visible: page.gains !== null
                Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.alignment: Qt.AlignTop
                Layout.preferredHeight: 70 + (page.gains ? page.gains.items.length : 0) * 40
                content: Column {
                    width: parent.width
                    Repeater {
                        model: page.gains ? page.gains.items : []
                        delegate: RowLayout {
                            required property var modelData
                            width: parent.width; height: 40
                            Text { text: modelData.name; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.fillWidth: true }
                            Text { text: "+" + modelData.today; color: studio.colors.ok; font.pixelSize: 15; font.weight: Font.Bold }
                            Text {
                                visible: modelData.total !== null
                                text: "total " + modelData.total
                                color: studio.colors.muted; font.pixelSize: 13
                                Layout.preferredWidth: 110; horizontalAlignment: Text.AlignRight
                            }
                        }
                    }
                }
            }
            Glass {
                title: "Failures"
                visible: page.failures !== null
                Layout.fillWidth: true; Layout.preferredWidth: 1; Layout.alignment: Qt.AlignTop
                Layout.preferredHeight: 70 + (page.failures ? page.failures.items.length : 0) * 40
                content: Column {
                    width: parent.width
                    Repeater {
                        model: page.failures ? page.failures.items : []
                        delegate: RowLayout {
                            required property var modelData
                            width: parent.width; height: 40; spacing: 12
                            Chip { text: Format.clock(modelData.time); tone: "danger" }
                            Text {
                                text: modelData.step + ": " + (modelData.reason || "failed")
                                color: studio.colors.text; font.pixelSize: 14
                                Layout.fillWidth: true; elide: Text.ElideRight
                            }
                        }
                    }
                }
            }
        }
    }

    function nowSteps() {
        if (!now || !now.path) return []
        return now.path.map(function (step) { return String(step).split(" > ").pop() })
    }
    function roundSummary() {
        var done = 0, total = 0
        for (var index = 0; index < round.steps.length; index++) {
            total++
            if (round.steps[index].state === "ok") done++
        }
        return done + " of " + total + " done in today's round"
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
