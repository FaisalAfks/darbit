// The Library's Screen view: each screen's last shot from Capture, with the targets taken on it in place, in their
// kinds' colours. A click on one opens it in the side panel; the search dims the others.
import QtQuick
import QtQuick.Layouts

Item {
    id: view
    property string chosenName: ""
    property string query: ""
    property string shownScreen: ""
    signal picked(string name, string kind)
    readonly property var screens: studio.screens
    readonly property var screen: {
        for (var index = 0; index < screens.length; index++)
            if (screens[index].screen === shownScreen) return screens[index]
        return screens.length ? screens[0] : null
    }
    readonly property var names: screen ? Object.keys(screen.assets) : []
    // the shown screen's saved shot when the chosen target was taken on it, for a retake on that shot
    readonly property string chosenShot: screen && screen.shot && screen.assets[chosenName] ? screen.shot : ""
    readonly property real fit: screen ? Math.min(shot.parent.width / screen.w, shot.parent.height / screen.h) : 1
    function inkOf(kind) { return kind === "region" ? studio.colors.kindRegion : kind === "location" ? studio.colors.kindLocation : studio.colors.kindImage }

    Column {
        visible: view.screens.length === 0
        anchors.centerIn: parent; spacing: 8
        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "No screens yet"; color: studio.colors.text; font.pixelSize: 20; font.weight: Font.Bold }
        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Capture keeps the screen each target was taken on, and shows it here."; color: studio.colors.muted; font.pixelSize: 14 }
    }

    ColumnLayout {
        visible: view.screens.length > 0
        anchors.fill: parent
        spacing: 12
        Segmented {
            strong: false; itemHeight: 30
            current: view.screen ? view.screen.screen : ""
            model: view.screens.map(function (one) { return { key: one.screen, label: one.screen, count: Object.keys(one.assets).length } })
            onPicked: function (key) { view.shownScreen = key }
        }
        Item {
            Layout.fillWidth: true; Layout.fillHeight: true
            Image {
                id: shot
                source: view.screen ? view.screen.picture : ""
                width: view.screen ? view.screen.w * view.fit : 0
                height: view.screen ? view.screen.h * view.fit : 0
                fillMode: Image.Stretch; asynchronous: true
                Repeater {
                    model: view.names
                    delegate: Rectangle {
                        id: mark
                        required property string modelData
                        readonly property var asset: view.screen.assets[modelData]
                        readonly property var box: asset.box || [0, 0, 0, 0]
                        readonly property bool on: view.chosenName === modelData
                        readonly property bool matches: view.query === "" || modelData.toLowerCase().indexOf(view.query.toLowerCase()) >= 0
                        readonly property color ink: view.inkOf(asset.kind)
                        x: box[0] * view.fit; y: box[1] * view.fit
                        width: Math.max(10, box[2] * view.fit); height: Math.max(10, box[3] * view.fit)
                        radius: asset.kind === "location" ? width / 2 : 3
                        color: on || area.containsMouse ? Qt.rgba(ink.r, ink.g, ink.b, 0.22) : "transparent"
                        border.color: ink; border.width: on ? 4 : 3
                        opacity: matches ? 1 : 0.2
                        MouseArea {
                            id: area
                            anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: view.picked(mark.modelData, mark.asset.kind)
                        }
                        Chip {
                            visible: area.containsMouse || mark.on
                            anchors { left: parent.left; bottom: parent.top; bottomMargin: 4 }
                            height: 20; z: 2
                            tone: "accent"; text: mark.modelData
                        }
                    }
                }
            }
        }
    }
}
