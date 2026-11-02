// A number between two limits as a slider, with its value beside it: for a setting that has both a min and a max.
import QtQuick
import QtQuick.Controls.Basic

Row {
    id: valueSlider
    property real value: 0
    property real low: 0
    property real high: 1
    property int decimals: 1
    property string unit: ""
    signal edited(real value)
    spacing: 10
    Slider {
        id: slider
        width: 150; height: 30
        from: valueSlider.low; to: valueSlider.high; value: valueSlider.value
        stepSize: Math.pow(10, -valueSlider.decimals)
        onMoved: valueSlider.edited(Number(value.toFixed(valueSlider.decimals)))
        background: Rectangle {
            x: slider.leftPadding; y: slider.topPadding + slider.availableHeight / 2 - height / 2
            width: slider.availableWidth; height: 4; radius: 2
            color: studio.colors.raisedHover
            Rectangle { width: slider.visualPosition * parent.width; height: parent.height; radius: 2; color: studio.colors.accent }
        }
        handle: Rectangle {
            x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
            y: slider.topPadding + slider.availableHeight / 2 - height / 2
            width: 16; height: 16; radius: 8
            color: studio.colors.text
            border.color: slider.activeFocus ? studio.colors.accent : "transparent"; border.width: 2
        }
    }
    Text {
        width: 52
        anchors.verticalCenter: parent.verticalCenter
        text: valueSlider.value.toFixed(valueSlider.decimals) + valueSlider.unit
        color: studio.colors.text; font.pixelSize: 13; font.family: "monospace"; font.weight: Font.DemiBold
    }
}
