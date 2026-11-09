// A picture drawn whole in its box and decoded at the size it's drawn, in the screen's pixels, not larger. Qt decodes
// at sourceSize times the screen's scale, and given both sides it fills the box instead of fitting it, so only the side
// that limits the fit is given. `pictureSize` is the picture's [width, height] when known; without it, the picture's
// shape is taken from its first load.
import QtQuick

Image {
    id: picture
    property var pictureSize: null
    property bool tall: false  // without pictureSize: the loaded picture is taller than its box
    readonly property bool heightLimits: pictureSize ? pictureSize[1] * width > pictureSize[0] * height : tall
    fillMode: Image.PreserveAspectFit
    asynchronous: true
    sourceSize: heightLimits ? Qt.size(0, Math.ceil(height)) : Qt.size(Math.ceil(width), 0)
    onStatusChanged: {
        if (status === Image.Ready && !pictureSize)
            tall = implicitHeight * width > implicitWidth * height
    }
}
