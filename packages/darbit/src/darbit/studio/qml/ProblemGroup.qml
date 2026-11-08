// One kind of problem on the Results page (round 13, C with A's detail): its likely cause, what failed and how often,
// the plain sentence of what the bot saw, and, opened (#317, C), the screen when it stopped with the closest match
// boxed and scored, the images it waited for (best against what each needs) and the steps before it, with the fixes:
// Retake on that screen or on the screen now. From server/problems.py.
import QtQuick
import QtQuick.Layouts
import "format.js" as Format

Rectangle {
    id: group
    property var problem: ({})
    property bool open: false
    signal hide()
    readonly property color ink: problem.tone === "info" ? studio.colors.info : problem.tone === "warn" ? studio.colors.warn : studio.colors.danger
    readonly property var searches: problem.searches || []
    readonly property var worst: searches.length ? searches[0] : null  // the image it waited for last: why it stopped
    // the screen shown: the one its closest match was seen on, else the one when it stopped
    readonly property string shot: worst && worst.screenshot ? worst.screenshot : (problem.screenshot || "")
    readonly property bool boxed: worst !== null && !!worst.at && !!worst.screenshot && shot === worst.screenshot
    readonly property var times: problem.times || []
    readonly property var before: problem.before || []
    implicitHeight: body.implicitHeight + 32
    radius: 16
    color: Qt.rgba(ink.r, ink.g, ink.b, 0.06)
    border.color: Qt.rgba(ink.r, ink.g, ink.b, 0.35)
    Behavior on implicitHeight { NumberAnimation { duration: studio.effects ? 220 : 0; easing.type: Easing.OutCubic } }
    clip: true

    function scoreColor(row) { return row.closest >= row.needs - 0.2 ? studio.colors.warn : studio.colors.danger }
    function seconds(time) { return String(time || "").split("T").pop().slice(0, 8) }  // "11:57:40"

    Column {
        id: body
        x: 18; y: 16; width: parent.width - 36
        spacing: 10
        // the head: its cause, what failed, how often and when; a click opens the evidence
        RowLayout {
            width: parent.width; spacing: 12
            Rectangle {
                Layout.preferredWidth: causeText.implicitWidth + 22; Layout.preferredHeight: 26; radius: 13
                color: Qt.rgba(group.ink.r, group.ink.g, group.ink.b, 0.16)
                border.color: Qt.rgba(group.ink.r, group.ink.g, group.ink.b, 0.5)
                Text { id: causeText; anchors.centerIn: parent; text: group.problem.label || ""; color: group.ink; font.pixelSize: 12; font.weight: Font.DemiBold }
            }
            Text {
                Layout.fillWidth: true; elide: Text.ElideRight
                text: (group.problem.step || "") + ": " + (group.problem.reason || "")
                color: studio.colors.text; font.pixelSize: 15; font.weight: Font.DemiBold
            }
            Text {
                text: (group.problem.count > 1 ? group.problem.count + " times · " : "")
                    + group.times.map(function (time) { return Format.clock(time) }).join(", ")
                color: studio.colors.muted; font.pixelSize: 12
            }
            IconButton { glyph: group.open ? "▴" : "▾"; tip: group.open ? "Less" : "What it saw"; onClicked: group.open = !group.open }
        }
        Text {
            width: parent.width; wrapMode: Text.Wrap
            text: group.problem.sentence || ""
            color: studio.colors.text; font.pixelSize: 13; lineHeight: 1.2
        }

        // the evidence, opened: the screen with the closest match on it and the retakes under it; beside it, the
        // images it waited for, the steps before it stopped and the other fixes
        RowLayout {
            visible: group.open
            width: parent.width; spacing: 20
            Column {
                Layout.preferredWidth: Math.round(parent.width * 0.6); Layout.alignment: Qt.AlignTop
                spacing: 12
                Rectangle {
                    width: parent.width; height: group.shot !== "" ? Math.round(width * 9 / 16) : 120
                    radius: 10; color: studio.colors.bg; border.color: studio.colors.line; clip: true
                    Image {
                        id: screenshot
                        anchors.fill: parent; anchors.margins: 1
                        source: group.shot; fillMode: Image.PreserveAspectFit; asynchronous: true
                    }
                    // the image it waited for, only for its size: the box is that big at the closest match
                    Image { id: wanted; visible: false; source: group.worst && group.worst.picture ? group.worst.picture : ""; asynchronous: true }
                    Item {
                        id: match
                        objectName: "closestMatch"
                        readonly property real scale: screenshot.implicitWidth > 0 ? screenshot.paintedWidth / screenshot.implicitWidth : 0
                        readonly property var at: group.boxed ? group.worst.at : [0, 0]
                        visible: group.boxed && scale > 0 && wanted.implicitWidth > 0
                        // matches are in screen pixels; the screenshot is the whole desktop, which may start left of 0
                        x: screenshot.x + (screenshot.width - screenshot.paintedWidth) / 2 + (at[0] - studio.desktopOrigin[0]) * scale
                        y: screenshot.y + (screenshot.height - screenshot.paintedHeight) / 2 + (at[1] - studio.desktopOrigin[1]) * scale
                        width: wanted.implicitWidth * scale; height: wanted.implicitHeight * scale
                        Rectangle {
                            anchors.fill: parent; anchors.margins: -2
                            color: "transparent"; radius: 3
                            border.width: 2; border.color: group.worst ? group.scoreColor(group.worst) : studio.colors.warn
                        }
                        Rectangle {
                            anchors { bottom: parent.top; bottomMargin: 6; horizontalCenter: parent.horizontalCenter }
                            width: scoreText.implicitWidth + 12; height: 20; radius: 5
                            color: group.worst ? group.scoreColor(group.worst) : studio.colors.warn
                            Text {
                                id: scoreText
                                anchors.centerIn: parent
                                text: group.worst ? "closest " + group.worst.closest.toFixed(2) + " of " + group.worst.needs.toFixed(2) : ""
                                color: studio.colors.onStatus; font.pixelSize: 11; font.weight: Font.DemiBold
                            }
                        }
                    }
                    Text {
                        visible: group.shot !== ""
                        x: 8; y: 6; text: "when it stopped · " + group.seconds(group.times[group.times.length - 1])
                        color: studio.colors.text; font.pixelSize: 10; font.family: "monospace"
                        style: Text.Outline; styleColor: studio.colors.bg
                    }
                    Text {
                        visible: group.shot === ""
                        anchors.centerIn: parent; width: parent.width - 40
                        horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
                        text: "No screenshot of this one"
                        color: studio.colors.faint; font.pixelSize: 13
                    }
                    MouseArea { anchors.fill: parent; enabled: group.shot !== ""; cursorShape: Qt.PointingHandCursor; onClicked: Qt.openUrlExternally(group.shot) }
                }
                Flow {
                    visible: !!group.problem.target
                    width: parent.width; spacing: 8
                    PillButton {
                        objectName: "retakeOnShot"
                        visible: group.shot !== ""
                        kind: "primary"; icon: "▣"; small: true
                        text: "Retake " + (group.problem.target || "") + " on this screen"
                        onClicked: studio.retakeOn(group.problem.target, "image", group.shot)
                    }
                    PillButton {
                        objectName: "retakeNow"
                        kind: group.shot === "" ? "primary" : "plain"; icon: "▣"; small: true
                        text: group.shot === "" ? "Retake " + (group.problem.target || "") + " on the screen now" : "Retake on the screen now"
                        onClicked: studio.retake(group.problem.target, "image")
                    }
                }
            }
            Column {
                Layout.fillWidth: true; Layout.alignment: Qt.AlignTop
                spacing: 10
                Text { text: "WAITED FOR"; color: studio.colors.muted; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.3 }
                Text {
                    visible: group.searches.length === 0
                    width: parent.width; wrapMode: Text.Wrap
                    text: "Nothing it looked for ran out before it stopped."
                    color: studio.colors.muted; font.pixelSize: 12
                }
                Repeater {
                    model: group.searches
                    delegate: RowLayout {
                        required property var modelData
                        width: parent.width; spacing: 12
                        Rectangle {
                            Layout.preferredWidth: 116; Layout.preferredHeight: 30; radius: 4; color: studio.colors.bg; clip: true
                            Image { anchors.fill: parent; source: modelData.picture || ""; fillMode: Image.PreserveAspectFit; asynchronous: true }
                        }
                        Column {
                            Layout.fillWidth: true
                            Text { width: parent.width; elide: Text.ElideRight; text: modelData.target; color: studio.colors.text; font.pixelSize: 13; font.family: "monospace"; font.weight: Font.DemiBold }
                            Text {
                                width: parent.width; elide: Text.ElideRight
                                text: "best " + modelData.closest.toFixed(2) + ", needs " + modelData.needs.toFixed(2) + " · looked " + Format.duration(modelData.seconds)
                                color: group.scoreColor(modelData); font.pixelSize: 12
                            }
                        }
                    }
                }
                Item { width: 1; height: 6 }
                Text { text: "BEFORE IT STOPPED"; color: studio.colors.muted; font.pixelSize: 11; font.weight: Font.DemiBold; font.letterSpacing: 1.3 }
                Text {
                    visible: group.before.length === 0
                    text: "Nothing it did is in the report before this."; color: studio.colors.muted; font.pixelSize: 12
                }
                Column {
                    width: parent.width
                    Repeater {
                        model: group.before
                        delegate: RowLayout {
                            required property var modelData
                            required property int index
                            readonly property bool last: index === group.before.length - 1
                            width: parent.width; height: 20; spacing: 10
                            Text { text: group.seconds(modelData.time); color: studio.colors.faint; font.pixelSize: 11; font.family: "monospace" }
                            Rectangle { width: 8; height: 8; radius: 4; color: modelData.ok ? studio.colors.ok : studio.colors.danger }
                            Text {
                                Layout.fillWidth: true; elide: Text.ElideRight
                                text: modelData.say
                                color: last ? studio.colors.text : studio.colors.muted
                                font.pixelSize: 12; font.weight: last ? Font.DemiBold : Font.Normal
                            }
                        }
                    }
                }
                Item { width: 1; height: 6 }
                // the other fixes
                Flow {
                    width: parent.width; spacing: 8
                    PillButton {
                        visible: !!group.problem.target
                        small: true; kind: "quiet"; icon: "◎"; text: "Highlight " + group.problem.target
                        onClicked: studio.highlightOne(group.problem.target)
                    }
                    PillButton {
                        visible: (group.problem.screenshots || []).length > 1
                        readonly property var shots: group.problem.screenshots || []
                        small: true; kind: "quiet"; icon: "▤"; text: "Screenshots (" + shots.length + ")"
                        onClicked: Qt.openUrlExternally(shots[shots.length - 1].replace(/[^/]*$/, ""))
                    }
                    PillButton { small: true; kind: "quiet"; text: "Not a problem"; onClicked: group.hide() }
                }
            }
        }
    }
}
