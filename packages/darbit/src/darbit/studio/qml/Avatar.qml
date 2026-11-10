// A bot's square: its own icon when darbit.toml gives one, cut to the square's rounded shape and decoded at the size
// it's drawn, in the screen's pixels; otherwise, and while the icon loads or when it can't be read, its accent (or
// darbit's) with its initials. The icon is drawn on a Canvas, which clips to the rounded shape on every renderer.
import QtQuick
import QtQuick.Window
import "format.js" as Format

Rectangle {
    id: avatar
    property string name: ""
    property string accent: ""
    property string icon: ""  // the icon's file URL (`icon` in the bot's listing); empty: the initials
    property int size: 32
    readonly property bool showsIcon: drawing.item !== null && drawing.item.drawn
    width: size; height: size; radius: size * 0.3
    color: showsIcon ? "transparent" : accent !== "" ? accent : studio.colors.accent2
    Text {
        visible: !avatar.showsIcon
        anchors.centerIn: parent
        text: Format.initials(parent.name)
        color: "#1a0b14"
        font.pixelSize: parent.size * 0.4; font.weight: Font.Bold
    }
    Loader {
        id: drawing
        anchors.fill: parent
        active: avatar.icon !== ""
        sourceComponent: Canvas {
            id: canvas
            property bool drawn: false
            property url loaded: ""
            // the icon decoded to cover the square (Qt's PreserveAspectCrop with both sides): its size here gives the
            // canvas's own copy, the same size, drawn centred and unscaled
            Image {
                id: shape
                visible: false
                source: avatar.icon
                fillMode: Image.PreserveAspectCrop
                sourceSize: Qt.size(avatar.size, avatar.size)
                asynchronous: true
                onStatusChanged: canvas.load()
            }
            function load() {
                if (loaded.toString() !== "")
                    unloadImage(loaded)
                drawn = false
                loaded = ""
                if (shape.status !== Image.Ready) {
                    requestPaint()  // clears what was drawn: the initials show
                    return
                }
                loaded = avatar.icon
                var ratio = Screen.devicePixelRatio
                loadImage(loaded, Qt.size(Math.ceil(shape.implicitWidth * ratio), Math.ceil(shape.implicitHeight * ratio)))
                if (isImageLoaded(loaded))
                    requestPaint()
            }
            onImageLoaded: requestPaint()
            onPaint: {
                var context = getContext("2d")
                context.reset()
                if (loaded.toString() === "" || !isImageLoaded(loaded))
                    return
                var w = shape.implicitWidth
                var h = shape.implicitHeight
                context.beginPath()
                context.roundedRect(0, 0, width, height, avatar.radius, avatar.radius)
                context.clip()
                context.drawImage(loaded, (width - w) / 2, (height - h) / 2, w, h)
                drawn = true
            }
        }
    }
}
