// Runs: one day at a time: how long each mode ran, what was gained, and what went wrong.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

Flickable {
    id: page
    property string chosen: ""
    contentHeight: column.height + 120
    clip: true
    ScrollBar.vertical: ScrollBar {}

    Connections {
        target: studio
        function onDaysChanged() {
            if (studio.days.length > 0 && (page.chosen === "" || !page.known(page.chosen))) page.pick(studio.days[0].day)
        }
    }
    function known(day) {
        return studio.days.some(function (row) { return row.day === day })
    }
    function pick(day) {
        chosen = day
        studio.loadDay(day)
    }

    // each mode's time: the lanes' blocks added up, longest first
    readonly property var modes: {
        var lanes = studio.day.lanes || [], found = []
        for (var index = 0; index < lanes.length; index++) {
            var total = 0, failed = 0, runs = 0, open = false
            for (var at = 0; at < lanes[index].blocks.length; at++) {
                var block = lanes[index].blocks[at]
                runs++
                if (block.state === "failed") failed++
                if (block.state === "running") open = true
                if (block.end !== null && block.start !== null) total += block.end - block.start
            }
            found.push({ name: lanes[index].name, seconds: total, runs: runs, failed: failed, open: open })
        }
        found.sort(function (a, b) { return b.seconds - a.seconds })
        return found
    }
    readonly property real longest: modes.length ? Math.max(1, modes[0].seconds) : 1

    ColumnLayout {
        id: column
        x: 24; width: page.width - 48
        spacing: 20

        RowLayout {
            spacing: 16
            Text { text: "Runs"; color: studio.colors.text; font.pixelSize: 30; font.weight: Font.Bold }
            Pill {
                height: 40
                visible: studio.days.length > 0
                Repeater {
                    model: studio.days.slice(0, 7)
                    delegate: Tab {
                        required property var modelData
                        required property int index
                        height: 30
                        label: index === 0 ? "Latest" : modelData.day.slice(5)
                        current: page.chosen === modelData.day
                        onClicked: page.pick(modelData.day)
                    }
                }
            }
        }

        Text {
            visible: studio.days.length === 0
            text: "No runs yet: what the bot does shows here once it has run."
            color: studio.colors.muted; font.pixelSize: 15
        }

        RowLayout {
            visible: studio.days.length > 0
            Layout.fillWidth: true
            spacing: 20

            Glass {
                title: (studio.day.day || "") + ", by mode"
                note: studio.day.start !== undefined && studio.day.start !== null
                    ? Format.duration(studio.day.end - studio.day.start) + " run" : ""
                Layout.fillWidth: true; Layout.preferredWidth: 3; Layout.alignment: Qt.AlignTop
                Layout.preferredHeight: 80 + page.modes.length * 36
                content: Column {
                    width: parent.width
                    Repeater {
                        model: page.modes
                        delegate: RowLayout {
                            required property var modelData
                            width: parent.width; height: 36; spacing: 18
                            Text { text: modelData.name; color: studio.colors.text; font.pixelSize: 14; Layout.preferredWidth: 170; elide: Text.ElideRight }
                            Bar {
                                Layout.fillWidth: true
                                share: modelData.seconds / page.longest
                                tint: modelData.failed > 0 && modelData.failed === modelData.runs ? studio.colors.danger : studio.colors.ok
                            }
                            Text {
                                Layout.preferredWidth: 90; horizontalAlignment: Text.AlignRight
                                text: modelData.open ? "running"
                                    : modelData.failed > 0 && modelData.failed === modelData.runs ? modelData.failed + " fail"
                                    : modelData.runs > 1 ? modelData.runs + " runs" : Format.duration(modelData.seconds)
                                color: studio.colors.muted; font.family: "monospace"; font.pixelSize: 13
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true; Layout.preferredWidth: 2; Layout.alignment: Qt.AlignTop
                spacing: 20
                Glass {
                    title: "Gains"
                    visible: (studio.day.gains || []).length > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70 + (studio.day.gains || []).length * 38
                    content: Column {
                        width: parent.width
                        Repeater {
                            model: studio.day.gains || []
                            delegate: RowLayout {
                                required property var modelData
                                width: parent.width; height: 38
                                Text { text: modelData.name; color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold; Layout.fillWidth: true }
                                Text { text: "+" + modelData.today; color: studio.colors.ok; font.pixelSize: 15; font.weight: Font.Bold }
                            }
                        }
                    }
                }
                Glass {
                    title: "Failures"
                    note: studio.day.lost_seconds ? Format.duration(studio.day.lost_seconds) + " lost" : ""
                    Layout.fillWidth: true
                    Layout.preferredHeight: 70 + Math.max(1, (studio.day.problems || []).length) * 56
                    content: Column {
                        width: parent.width; spacing: 8
                        Text {
                            visible: (studio.day.problems || []).length === 0
                            text: "Nothing went wrong."; color: studio.colors.muted; font.pixelSize: 14
                        }
                        Repeater {
                            model: studio.day.problems || []
                            delegate: Rectangle {
                                required property var modelData
                                width: parent.width; height: 48; radius: 10
                                color: studio.colors.raised
                                RowLayout {
                                    anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
                                    spacing: 10
                                    Chip { text: "×" + modelData.count; tone: "danger" }
                                    Text {
                                        text: modelData.step + ": " + (modelData.reason || "failed")
                                        color: studio.colors.text; font.pixelSize: 14
                                        Layout.fillWidth: true; elide: Text.ElideRight
                                    }
                                    Text { text: Format.clock(modelData.times[modelData.times.length - 1]); color: studio.colors.muted; font.pixelSize: 13 }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
