// A number with − and +: a step at a time (Shift: ten), kept inside its range; the number itself can be typed.
import QtQuick
import QtQuick.Controls.Basic

Rectangle {
    id: stepper
    property real value: 0
    property real step: 1
    property var low: null        // the smallest it takes; null for no limit
    property var high: null
    property int decimals: 0
    property string unit: ""
    signal edited(real value)
    implicitWidth: minus.width + field.width + (unit !== "" ? unitText.implicitWidth + 4 : 0) + plus.width + 4
    implicitHeight: 34
    radius: 10
    color: studio.colors.raised
    border.color: field.activeFocus ? studio.colors.accent : studio.colors.line

    function fit(next) {
        if (low !== null && next < low) next = low
        if (high !== null && next > high) next = high
        return Number(next.toFixed(decimals))
    }
    function nudge(steps) { stepper.edited(fit(stepper.value + steps * stepper.step)) }

    Row {
        anchors.centerIn: parent
        IconButton {
            id: minus; width: 30; height: 30; glyph: "−"; tip: ""
            enabled: stepper.low === null || stepper.value > stepper.low
            onClicked: stepper.nudge(-1)
        }
        TextField {
            id: field
            width: Math.max(44, contentWidth + 18); height: 30
            horizontalAlignment: TextInput.AlignHCenter
            text: stepper.value.toFixed(stepper.decimals)
            color: studio.colors.text; font.pixelSize: 13; font.family: "monospace"; font.weight: Font.DemiBold
            inputMethodHints: Qt.ImhFormattedNumbersOnly
            background: null
            onEditingFinished: { var typed = parseFloat(text); if (!isNaN(typed)) stepper.edited(stepper.fit(typed)); text = Qt.binding(function () { return stepper.value.toFixed(stepper.decimals) }) }
            Keys.onUpPressed: function (event) { stepper.nudge(event.modifiers & Qt.ShiftModifier ? 10 : 1) }
            Keys.onDownPressed: function (event) { stepper.nudge(event.modifiers & Qt.ShiftModifier ? -10 : -1) }
        }
        Text { id: unitText; visible: stepper.unit !== ""; text: stepper.unit; color: studio.colors.faint; font.pixelSize: 12; anchors.verticalCenter: parent.verticalCenter; rightPadding: 4 }
        IconButton {
            id: plus; width: 30; height: 30; glyph: "+"; tip: ""
            enabled: stepper.high === null || stepper.value < stepper.high
            onClicked: stepper.nudge(1)
        }
    }
}
