// The chosen asset, in full: its picture, its numbers, its last scores, Retake, Rename and Delete, and where it's used.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: panel
    property var asset: null
    property var score: null
    property real needs: 0.9
    property string kindLabel: ""
    property bool renaming: false
    property bool confirming: false
    signal closed()
    signal renamed(string to)
    signal deleted()
    onAssetChanged: { renaming = false; confirming = false }
    radius: 18
    color: studio.colors.glassStrong
    border.color: studio.colors.line
    clip: true

    Flickable {
        anchors.fill: parent; anchors.margins: 18
        contentHeight: body.height
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ColumnLayout {
            id: body
            width: parent.width
            spacing: 14
            visible: panel.asset !== null

            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 170
                radius: 12; color: studio.colors.bg
                Image {
                    anchors.fill: parent; anchors.margins: 10
                    source: panel.asset && panel.asset.thumbnail ? panel.asset.thumbnail : ""
                    sourceSize: Qt.size(600, 340)
                    fillMode: Image.PreserveAspectFit; asynchronous: true
                }
                PillButton {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 8
                    icon: "✕"; kind: "quiet"; small: true
                    onClicked: panel.closed()
                }
            }
            Column {
                Layout.fillWidth: true
                spacing: 4
                Text { width: parent.width; text: panel.asset ? panel.asset.name : ""; color: studio.colors.text; font.pixelSize: 18; font.weight: Font.Bold; wrapMode: Text.WrapAnywhere }
                Text {
                    text: panel.asset ? panel.kindLabel + (panel.asset.size ? " · " + panel.asset.size[0] + " × " + panel.asset.size[1] : "")
                        + (panel.asset.region ? " · searched in its area" : "") : ""
                    color: studio.colors.muted; font.pixelSize: 13
                }
            }
            RowLayout {
                visible: panel.asset !== null && panel.asset.kind === "image"
                Layout.fillWidth: true; spacing: 8
                Repeater {
                    model: [
                        { label: "Score", value: panel.score === null ? "—" : panel.score.toFixed(2) },
                        { label: "Needs", value: panel.needs.toFixed(2) },
                        { label: "Used", value: panel.asset ? (panel.asset.uses || 0) + "×" : "" }
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        Layout.fillWidth: true; height: 58; radius: 12; color: studio.colors.raised
                        Column {
                            x: 12; anchors.verticalCenter: parent.verticalCenter
                            Text { text: modelData.label; color: studio.colors.faint; font.pixelSize: 12 }
                            Text { text: modelData.value; color: studio.colors.text; font.pixelSize: 17; font.weight: Font.Bold }
                        }
                    }
                }
            }
            Column {  // its last scores, oldest first
                visible: panel.asset !== null && panel.asset.scores && panel.asset.scores.length > 0
                Layout.fillWidth: true; spacing: 6
                Text { text: "Last runs"; color: studio.colors.muted; font.pixelSize: 13 }
                Row {
                    spacing: 4
                    Repeater {
                        model: panel.asset && panel.asset.scores ? panel.asset.scores.slice(-14) : []
                        delegate: Rectangle {
                            required property var modelData
                            width: 15; height: 24; radius: 4
                            color: modelData >= panel.needs + 0.05 ? studio.colors.ok : modelData >= panel.needs ? studio.colors.warn : studio.colors.danger
                            opacity: 0.85
                        }
                    }
                }
            }
            GridLayout {
                Layout.fillWidth: true
                columns: 2; columnSpacing: 8; rowSpacing: 8
                PillButton { Layout.fillWidth: true; icon: "▣"; text: "Retake"; onClicked: studio.retake(panel.asset.name, panel.asset.kind === "location" ? "point" : panel.asset.kind) }
                PillButton { Layout.fillWidth: true; icon: "✎"; text: "Rename"; onClicked: { panel.renaming = true; nameField.text = panel.asset.name; nameField.forceActiveFocus() } }
            }
            RowLayout {
                visible: panel.renaming
                Layout.fillWidth: true; spacing: 8
                TextField {
                    id: nameField
                    Layout.fillWidth: true; Layout.preferredHeight: 38
                    color: studio.colors.text; font.pixelSize: 14
                    onAccepted: if (text.trim() !== "" && text.trim() !== panel.asset.name) panel.renamed(text.trim())
                    Keys.onEscapePressed: panel.renaming = false
                    background: Rectangle { radius: 10; color: studio.colors.raised; border.color: studio.colors.accent }
                }
                PillButton { text: "Rename"; kind: "primary"; small: true; onClicked: nameField.accepted() }
            }
            Text {
                visible: panel.renaming
                Layout.fillWidth: true; wrapMode: Text.Wrap
                text: "Every line in the bot's code that names it changes too."
                color: studio.colors.faint; font.pixelSize: 12
            }
            Column {
                Layout.fillWidth: true; spacing: 6
                visible: studio.uses.length > 0
                Text { text: "Used in " + studio.uses.length + (studio.uses.length === 1 ? " place" : " places"); color: studio.colors.muted; font.pixelSize: 13 }
                Repeater {
                    model: studio.uses.slice(0, 12)
                    delegate: Text {
                        required property var modelData
                        width: parent.width; elide: Text.ElideMiddle
                        text: modelData.file + ":" + modelData.line
                        color: studio.colors.text; font.family: "monospace"; font.pixelSize: 12
                    }
                }
            }
            PillButton {
                Layout.fillWidth: true
                kind: "danger"; icon: "🗑"; text: panel.confirming ? "Delete it and its files" : "Delete…"
                onClicked: panel.confirming ? panel.deleted() : panel.confirming = true
            }
        }
    }
}
