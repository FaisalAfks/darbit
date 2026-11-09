// What a card has under the mouse (CardMotion, through a Loader): a soft drop shadow and an accent glow, both outside the card only, so
// the glass doesn't darken. Loaded only while the mouse is on a card.
import QtQuick
import QtQuick.Effects

Item {
    id: shade
    readonly property Item card: parent ? parent.parent : null  // the card's CardMotion (its Loader's parent)
    readonly property real room: 48  // how far the shadow reaches past the card
    Item {
        id: shadows
        anchors.fill: parent
        visible: false
        layer.enabled: true
        RectangularShadow {
            x: shade.room; y: shade.room + 10; width: (shade.card ? shade.card.width : 0); height: (shade.card ? shade.card.height : 0)
            radius: (shade.card ? shade.card.radius : 0); blur: 28
            color: studio.colors.shadow
        }
        RectangularShadow {
            x: shade.room; y: shade.room; width: (shade.card ? shade.card.width : 0); height: (shade.card ? shade.card.height : 0)
            radius: (shade.card ? shade.card.radius : 0); blur: 18
            color: Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.28)
        }
    }
    Item {
        id: cardShape
        anchors.fill: parent
        visible: false
        layer.enabled: true
        Rectangle { x: shade.room; y: shade.room; width: (shade.card ? shade.card.width : 0); height: (shade.card ? shade.card.height : 0); radius: (shade.card ? shade.card.radius : 0); color: "black" }
    }
    MultiEffect {
        anchors.fill: parent
        source: shadows
        maskEnabled: true
        maskSource: cardShape
        maskInverted: true
    }
}
