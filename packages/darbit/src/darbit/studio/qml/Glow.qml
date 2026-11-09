// A soft accent glow round its parent (a selection light while it moves). Loaded only while it shows, by a Loader with
// this file as its source, so the effects module is loaded only once something glows.
import QtQuick
import QtQuick.Effects

RectangularShadow {
    readonly property Item lit: parent ? parent.parent : null  // what glows (its Loader's parent)
    anchors.fill: parent
    radius: lit ? lit.radius : 0
    blur: 18
    color: Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.3)
}
