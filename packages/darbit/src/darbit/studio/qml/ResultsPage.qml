// Results: a bot's days, newest first; the chosen day as one sentence, its problems, what it got (today and the week)
// and a timeline of its modes. From the run history (SQLite), so a day of any size opens at once.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

Item {
    id: page
    property string chosen: ""
    Connections {
        target: studio
        function onDaysChanged() {
            var known = studio.days.some(function (row) { return row.day === page.chosen })
            if (studio.days.length > 0 && !known) page.pick(studio.days[0].day)
        }
    }
    function pick(day) { chosen = day; studio.loadDay(day) }
    readonly property var day: studio.day
    readonly property var gains: day.gains || []
    readonly property var problems: day.problems || []
    readonly property var lanes: day.lanes || []
    readonly property real span: day.start !== undefined && day.start !== null ? Math.max(60, day.end - day.start) : 0

    Text {
        visible: studio.days.length === 0
        anchors.centerIn: parent
        text: "No runs yet: what the bot does shows here once it has run."
        color: studio.colors.muted; font.pixelSize: 15
    }

    // ---- the days
    ListView {
        id: days
        visible: studio.days.length > 0
        x: 24; width: 236
        anchors { top: parent.top; bottom: parent.bottom; bottomMargin: 24 }
        spacing: 6
        clip: true
        model: studio.days
        delegate: Rectangle {
            required property var modelData
            readonly property bool on: modelData.day === page.chosen
            width: days.width; height: 64; radius: 14
            color: on ? Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.12) : area.containsMouse ? studio.colors.raised : "transparent"
            border.color: on ? Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.5) : "transparent"
            Behavior on color { ColorAnimation { duration: studio.effects ? 120 : 0 } }
            Column {
                x: 14; anchors.verticalCenter: parent.verticalCenter
                Row {
                    spacing: 8
                    Text { text: Format.dayName(modelData.day); color: studio.colors.text; font.pixelSize: 15; font.weight: Font.DemiBold }
                    Rectangle { visible: modelData.problems > 0; width: 7; height: 7; radius: 3.5; color: studio.colors.danger; anchors.verticalCenter: parent.verticalCenter }
                }
                Text { text: Format.duration(modelData.seconds) + (modelData.problems ? " · " + modelData.problems + (modelData.problems === 1 ? " problem" : " problems") : ""); color: studio.colors.muted; font.pixelSize: 12 }
            }
            Text {
                visible: !!modelData.lead
                anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
                text: modelData.lead ? "+" + modelData.lead.amount : ""
                color: studio.colors.ok; font.pixelSize: 14; font.weight: Font.Bold
            }
            MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: page.pick(modelData.day) }
        }
    }

    // ---- the chosen day
    Flickable {
        visible: studio.days.length > 0
        anchors { left: days.right; leftMargin: 16; right: parent.right; rightMargin: 24; top: parent.top; bottom: parent.bottom }
        contentHeight: column.height + 40
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}
        ColumnLayout {
            id: column
            width: parent.width
            spacing: 16

            Glass {
                Layout.fillWidth: true; Layout.preferredHeight: sentence.implicitHeight + 92
                padding: 24
                content: Column {
                    width: parent.width; spacing: 10
                    Row {
                        spacing: 12
                        Text { text: Format.dayName(page.day.day || ""); color: studio.colors.text; font.pixelSize: 24; font.weight: Font.Bold }
                        Text {
                            anchors.baseline: parent.children[0].baseline
                            text: page.span ? Format.clockOf(page.day.start) + " – " + Format.clockOf(page.day.end) : ""
                            color: studio.colors.faint; font.pixelSize: 13
                        }
                    }
                    Text {
                        id: sentence
                        width: parent.width; wrapMode: Text.Wrap
                        textFormat: Text.StyledText
                        color: studio.colors.muted; font.pixelSize: 17
                        text: page.summary()
                    }
                }
            }
            Repeater {
                model: page.problems
                delegate: Banner {
                    required property var modelData
                    Layout.fillWidth: true
                    tone: "danger"; icon: "×" + modelData.count
                    title: modelData.step + ": " + (modelData.reason || "failed")
                    detail: "last at " + Format.clock(modelData.times[modelData.times.length - 1])
                }
            }
            Glass {
                title: "What it got"
                note: "today · the week · total"
                delay: 60
                visible: page.gains.length > 0 || (page.day.progress || []).length > 0
                Layout.fillWidth: true
                Layout.preferredHeight: 72 + (page.gains.length + (page.day.progress || []).length) * 46
                content: Column {
                    width: parent.width
                    Repeater {
                        model: page.gains
                        delegate: RowLayout {
                            id: gainRow
                            required property var modelData
                            readonly property real most: Math.max.apply(null, (modelData.week || []).concat([1]))
                            width: parent.width; height: 46; spacing: 16
                            Rectangle { width: 10; height: 10; rotation: 45; radius: 2; color: studio.colors.accent2 }
                            Text { text: modelData.name; color: studio.colors.text; font.pixelSize: 15; font.weight: Font.DemiBold; Layout.fillWidth: true }
                            Text { text: "+" + modelData.today; color: studio.colors.ok; font.pixelSize: 15; font.weight: Font.Bold; Layout.preferredWidth: 70; horizontalAlignment: Text.AlignRight }
                            Row {  // the week, a bar a day
                                spacing: 3
                                Layout.preferredWidth: 7 * 17
                                Repeater {
                                    model: modelData.week
                                    delegate: Rectangle {
                                        required property var modelData
                                        required property int index
                                        width: 14; height: 26; radius: 3; color: studio.colors.raised
                                        Rectangle {
                                            anchors.bottom: parent.bottom; width: parent.width; radius: 3
                                            height: Math.max(2, parent.height * modelData / gainRow.most)
                                            color: index === 6 ? studio.colors.accent : Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.45)
                                        }
                                    }
                                }
                            }
                            Text { text: modelData.total !== null ? Number(modelData.total).toLocaleString(Qt.locale(), "f", 0) : ""; color: studio.colors.faint; font.pixelSize: 13; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight }
                        }
                    }
                    Repeater {
                        model: page.day.progress || []
                        delegate: RowLayout {
                            required property var modelData
                            width: parent.width; height: 46; spacing: 16
                            Text { text: "✓"; color: studio.colors.ok; font.pixelSize: 13 }
                            Text { text: modelData.label; color: studio.colors.text; font.pixelSize: 15; Layout.fillWidth: true }
                            Bar { Layout.preferredWidth: 200; share: modelData.total > 0 ? modelData.done / modelData.total : 0; gradientFill: true }
                            Text { text: modelData.done + " / " + modelData.total; color: studio.colors.faint; font.pixelSize: 13; Layout.preferredWidth: 80; horizontalAlignment: Text.AlignRight }
                        }
                    }
                }
            }
            Glass {
                title: "Timeline"
                delay: 120
                visible: page.lanes.length > 0 && page.span > 0
                Layout.fillWidth: true
                Layout.preferredHeight: 92 + page.lanes.length * 34
                content: Item {
                    width: parent.width; height: parent.height
                    Repeater {  // the hours along the top
                        model: 6
                        delegate: Text {
                            required property int index
                            x: 130 + (parent.width - 130) * index / 5 - width / 2
                            text: Format.clockOf(page.day.start + page.span * index / 5)
                            color: studio.colors.faint; font.pixelSize: 11
                        }
                    }
                    Repeater {
                        model: page.lanes
                        delegate: Item {
                            required property var modelData
                            required property int index
                            y: 24 + index * 34; width: parent.width; height: 26
                            Text { width: 120; text: modelData.name; color: studio.colors.text; font.pixelSize: 13; elide: Text.ElideRight; anchors.verticalCenter: parent.verticalCenter }
                            Rectangle {
                                id: lane
                                x: 130; width: parent.width - 130; height: parent.height; radius: 6
                                color: studio.colors.raised
                                Repeater {
                                    model: modelData.blocks
                                    delegate: Rectangle {
                                        required property var modelData
                                        readonly property real end: modelData.end !== null && modelData.end !== undefined ? modelData.end : (page.day.end || modelData.start)
                                        x: lane.width * (modelData.start - page.day.start) / page.span
                                        width: Math.max(4, lane.width * (end - modelData.start) / page.span)
                                        height: lane.height; radius: 6
                                        color: modelData.state === "failed" ? studio.colors.danger : modelData.state === "running" ? studio.colors.accent : studio.colors.ok
                                        opacity: 0.85
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    function summary() {
        if (!page.span) return ""
        var parts = ["Ran <b>" + Format.duration(page.span) + "</b>"]
        if (page.gains.length) {
            var got = page.gains.map(function (gain) { return "<font color='" + studio.colors.ok + "'><b>+" + gain.today + " " + gain.name.toLowerCase() + "</b></font>" })
            parts.push("and got " + got.join(" and "))
        }
        var text = parts.join(" ") + "."
        var finished = page.day.finished || {}
        if (finished.total) text += " It finished <b>" + Math.round(100 * finished.done / finished.total) + "%</b> of what it started"
        if (page.day.lost_seconds) text += " and lost about <b>" + Format.duration(page.day.lost_seconds) + "</b> to problems"
        return text + (finished.total ? "." : "")
    }
}
