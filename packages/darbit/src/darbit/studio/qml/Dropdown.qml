// One of a few choices, as a list that drops down: drawn in the Studio's look instead of Qt's.
import QtQuick
import QtQuick.Controls.Basic

ComboBox {
    id: dropdown
    property var choices: []
    property var chosen
    signal picked(var value)
    model: choices
    currentIndex: choices.indexOf(chosen)
    implicitWidth: Math.max(130, contentItem.implicitWidth + 44)
    implicitHeight: 34
    onActivated: function (index) { dropdown.picked(choices[index]) }
    contentItem: Text {
        leftPadding: 12
        text: dropdown.displayText
        color: studio.colors.text; font.pixelSize: 13; font.weight: Font.DemiBold
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    indicator: Text { x: dropdown.width - width - 12; anchors.verticalCenter: parent.verticalCenter; text: "▾"; color: studio.colors.muted; font.pixelSize: 11 }
    background: Rectangle {
        radius: 10; color: dropdown.hovered ? studio.colors.raisedHover : studio.colors.raised
        border.color: dropdown.activeFocus ? studio.colors.accent : studio.colors.line
    }
    popup: MenuPanel {
        y: dropdown.height + 4
        width: Math.max(dropdown.width, 180)
        padding: 6
        contentItem: ListView {
            implicitHeight: contentHeight
            model: dropdown.popup.visible ? dropdown.delegateModel : null
            clip: true
        }
    }
    delegate: ItemDelegate {
        required property var modelData
        required property int index
        width: dropdown.popup.width - 12; height: 34
        highlighted: dropdown.highlightedIndex === index
        contentItem: Text {
            text: String(modelData)
            color: index === dropdown.currentIndex ? studio.colors.accent : studio.colors.text
            font.pixelSize: 13; font.weight: Font.DemiBold; verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle { radius: 8; color: highlighted ? studio.colors.raisedHover : "transparent" }
    }
}
