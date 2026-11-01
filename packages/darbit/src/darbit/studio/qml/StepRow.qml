// One step of an action, read like what it does: its icon, one plain line, its line in the file, and (while
// editing) a wait's seconds, Up, Down and Remove. Loops and ifs hold their steps indented. It glows while Play is on it.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "format.js" as Format

Column {
    id: row
    property var step: ({})
    property bool followed: false  // this action is the one playing: a step glows when Play is on its line
    readonly property bool playingHere: followed && step.line > 0 && studio.playing.line === step.line
    property int depth: 0
    signal changed(var step)
    signal moved(int by)
    signal removed()
    readonly property color ink: step.kind === "call" ? studio.colors.slotBot : step.kind === "check" ? studio.colors.accent2
        : step.kind === "tape" ? studio.colors.accent : step.kind === "wait" ? studio.colors.faint : studio.colors.muted

    Rectangle {
        width: row.width; height: 44; radius: 10
        color: row.playingHere ? Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.16)
            : hover.hovered ? studio.colors.raised : "transparent"
        border.color: row.playingHere ? studio.colors.accent : "transparent"
        Behavior on color { ColorAnimation { duration: studio.effects ? 120 : 0 } }
        HoverHandler { id: hover }
        RowLayout {
            anchors { fill: parent; leftMargin: 12 + row.depth * 22; rightMargin: 10 }
            spacing: 12
            Text { text: Format.stepIcon(row.step); color: row.ink; font.pixelSize: 14; Layout.preferredWidth: 20; horizontalAlignment: Text.AlignHCenter }
            Text {
                text: Format.stepText(row.step)
                color: row.step.kind === "code" ? studio.colors.muted : studio.colors.text
                font.family: row.step.kind === "code" ? "monospace" : Qt.application.font.family
                font.pixelSize: 14; font.weight: row.step.kind === "call" ? Font.DemiBold : Font.Normal
                elide: Text.ElideRight; Layout.fillWidth: true
            }
            TextField {  // a wait's seconds, edited in place
                visible: row.step.kind === "wait" && hover.hovered
                Layout.preferredWidth: 70; Layout.preferredHeight: 30
                text: row.step.args ? String(row.step.args.seconds) : ""
                color: studio.colors.text; font.pixelSize: 13
                validator: DoubleValidator { bottom: 0 }
                onEditingFinished: {
                    var copy = JSON.parse(JSON.stringify(row.step))
                    copy.args.seconds = Number(text)
                    if (copy.args.seconds !== row.step.args.seconds) row.changed(copy)
                }
                background: Rectangle { radius: 8; color: studio.colors.raised; border.color: studio.colors.line }
            }
            Text { visible: !!row.step.note; text: "# " + (row.step.note || ""); color: studio.colors.faint; font.pixelSize: 12; Layout.maximumWidth: 220; elide: Text.ElideRight }
            Row {
                visible: hover.hovered
                spacing: 2
                IconButton { width: 28; height: 28; glyph: "↑"; tip: "Up"; onClicked: row.moved(-1) }
                IconButton { width: 28; height: 28; glyph: "↓"; tip: "Down"; onClicked: row.moved(1) }
                IconButton { width: 28; height: 28; glyph: "✕"; tip: "Remove"; onClicked: row.removed() }
            }
            Text { text: row.step.line ? row.step.line : "new"; color: studio.colors.faint; font.family: "monospace"; font.pixelSize: 11; Layout.preferredWidth: 30; horizontalAlignment: Text.AlignRight }
        }
    }
    Repeater {  // a loop's or an if's own steps (a Loader: a component can't hold itself directly)
        model: row.step.children || []
        delegate: Loader {
            id: inner
            required property var modelData
            required property int index
            width: row.width
            source: "StepRow.qml"
            onLoaded: {
                item.step = Qt.binding(function () { return inner.modelData })
                item.depth = row.depth + 1
                item.followed = Qt.binding(function () { return row.followed })
                item.changed.connect(function (changed) {
                    var copy = JSON.parse(JSON.stringify(row.step)); copy.children[inner.index] = changed; row.changed(copy)
                })
                item.removed.connect(function () {
                    var copy = JSON.parse(JSON.stringify(row.step)); copy.children.splice(inner.index, 1); row.changed(copy)
                })
                item.moved.connect(function (by) {
                    var copy = JSON.parse(JSON.stringify(row.step)), to = inner.index + by
                    if (to < 0 || to >= copy.children.length) return
                    var one = copy.children.splice(inner.index, 1)[0]; copy.children.splice(to, 0, one); row.changed(copy)
                })
            }
        }
    }
}
